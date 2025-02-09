from enum import Enum
from typing import Any, List, Optional, TypedDict, cast
from datetime import datetime, timedelta

from loguru import logger
from catalog.common.models import IdType, Item
from catalog.common.sites import SiteManager
from journal.models.common import VisibilityType
from journal.models.mark import Mark
from journal.models.shelf import ShelfType
from users.models import Task
from steam.webapi import WebAPI
from django.utils import timezone

# with reference to
# - https://developer.valvesoftware.com/wiki/Steam_Web_API
# - https://steamapi.xpaw.me/
#
# Get played (owned) games from IPlayerService.GetOwnedGames
# Get wishlist games from IWishlistService/GetWishlist

class ImportStatus(Enum):
    UNDERTERMINED = 1
    SKIPPED = 2
    IMPORTED = 3
    FAILED = 4

class RawGameMark(TypedDict):
    item: Item | None
    shelf_type: ShelfType | None
    created_time: datetime | None
    status: ImportStatus
    raw_entry: Any

class SteamImporter(Task):
    class MetaData(TypedDict):
        shelf_type_reversion: bool # allow cases like PROGRESS to WISHLIST
        fetch_wishlist: bool
        fetch_owned: bool
        last_play_to_ctime: bool # False: use current time
        total: int
        skipped: int
        processed: int
        failed: int
        imported: int
        visibility: VisibilityType
        failed_appids: List[str]
        steam_apikey: Optional[str]
        steam_id: Optional[int]

    DefaultMetadata: MetaData = {
        "shelf_type_reversion": False,
        "fetch_wishlist": True,
        "fetch_owned": True,
        "last_play_to_ctime": True,
        "total": 0,
        "skipped": 0,
        "processed": 0,
        "failed": 0,
        "imported": 0,
        "visibility": VisibilityType.Private,
        "failed_appids": [],
        "steam_apikey": None,
        "steam_id": None
    }

    def run(self):
        """
        Run task: fetch wishlist and/or owned games and import marks
        """
        fetched_raw_marks: List[RawGameMark] = []
        if self.metadata["fetch_wishlist"]: fetched_raw_marks.extend(self.get_wishlist_games())
        if self.metadata["fetch_owned"]: fetched_raw_marks.extend(self.get_owned_games())
        self.metadata["total"] = len(fetched_raw_marks)
        self.import_marks(fetched_raw_marks)
        self.message = f"""
        Steam importing complete, total: {self.metadata["total"]}, processed: {self.metadata["processed"]}, imported: {self.metadata["imported"]}, failed: {self.metadata["failed"]}, skipped: {self.metadata["skipped"]}
        """
        self.save()

    def import_marks(self, raw_marks: List[RawGameMark]):
        """
        Try import a list of RawGameMark as mark, scrape corresponding games if unavailable,
        and change status to one of ImportStatus.FAILED/IMPORTED/SKIPPED

        :param raw_marks: marks to import
        """

        for raw_mark in raw_marks:
            if any(v is None for v in raw_mark.values()): # skip none entry
                raw_mark["status"] = ImportStatus.FAILED
                logger.error(f"This raw mark cannot be added for None item / created_time / shelf_type: {raw_mark}")
                self.metadata["failed"] += 1
                self.metadata["processed"] += 1;
                continue
            if raw_mark["status"] != ImportStatus.UNDERTERMINED:
                logger.info(f"Rawmark of {raw_mark} already processed")
                continue

            mark = Mark(self.user.identity, cast(Item, raw_mark["item"]))

            if (not self.metadata["shelf_type_reversion"] # if reversion is not allowed, then skip marked entry with reversion
                and (
                    mark.shelf_type == ShelfType.COMPLETE
                    or (mark.shelf_type in [ShelfType.PROGRESS, ShelfType.DROPPED]
                        and raw_mark["shelf_type"] == ShelfType.WISHLIST
                    )
                )
            ):
                logger.info(f"Game {mark.item.title} is already marked, skipping.")
                raw_mark["status"] = ImportStatus.SKIPPED
                self.metadata["skipped"] += 1;
            else:
                mark.update(shelf_type=raw_mark['shelf_type'], visibility=self.metadata["visibility"], created_time=raw_mark['created_time'])
                raw_mark["status"] = ImportStatus.IMPORTED
                self.metadata["imported"] += 1;

            self.metadata["processed"] += 1;


    # NOTE: undocumented api used
    def get_wishlist_games(self) -> List[RawGameMark]:
        """
        From IWishlistService/GetWishlist, fetch wishlist of `steam_id` in self.metadata, and convert to RawGameMarks

        :return: Parsed list of raw game marked
        """
        steam_apikey: str = self.metadata["steam_apikey"]
        steam_id: int = self.metadata["steam_id"]
        webapi = WebAPI(steam_apikey)

        res = webapi.call(
            "IWishlistService.GetWishlist",
            steamid=steam_id
        )["response"]

        wishlist_rawmarks: List[RawGameMark] = []
        for entry in res["items"]:
            item = self.get_item_by_id(entry["appid"])
            created_time = datetime.fromtimestamp(entry["date_added"])
            if item is not None:
                wishlist_rawmarks.append({
                    "item": item,
                    "shelf_type": ShelfType.WISHLIST,
                    "created_time": created_time,
                    "status": ImportStatus.UNDERTERMINED,
                    "raw_entry": entry
                })
            else:
                wishlist_rawmarks.append({
                    "item": None,
                    "shelf_type": None,
                    "created_time": None,
                    "status": ImportStatus.FAILED,
                    "raw_entry": entry
                })

        return wishlist_rawmarks

    def get_owned_games(self, estimate_shelf_type: bool = True) -> List[RawGameMark]:
        """
        From IPlayerService.GetOwnedGames, fetch owned games of `steam_id` in self.metadata, and convert to RawGameMarks

        :return: Parsed list of raw game marked
        """
        steam_apikey: str = self.metadata["steam_apikey"]
        steam_id: int = self.metadata["steam_id"]
        webapi = WebAPI(steam_apikey)

        res = webapi.call(
            "IPlayerService.GetOwnedGames",
            format="json",
            steamid=steam_id,
            include_appinfo=True,
            include_played_free_games=True,
            appids_filter=[],
            include_free_sub=True,
            language="en",
            include_extended_appinfo=True,
        )["response"]

        owned_rawmarks: List[RawGameMark] = []
        for entry in res["games"]:
            item = self.get_item_by_id(entry["appid"])
            if estimate_shelf_type:
                shelf_type = SteamImporter.estimate_shelf_type(entry["playtime_forever"], datetime.fromtimestamp(entry["rtime_last_played"]), entry["appid"])
            else:
                shelf_type = ShelfType.COMPLETE
            # TODO: Fix such case: the game is purchased and never played, so rtime is 0, and we have no wishlist
            created_time = datetime.fromtimestamp(entry["rtime_last_played"]) if self.metadata["last_play_to_ctime"] else timezone.now()
            if item is not None:
                owned_rawmarks.append({
                    "item": item,
                    "shelf_type": shelf_type,
                    "created_time": created_time,
                    "status": ImportStatus.UNDERTERMINED,
                    "raw_entry": entry
                })
            else:
                owned_rawmarks.append({
                    "item": None,
                    "shelf_type": None,
                    "created_time": None,
                    "status": ImportStatus.FAILED,
                    "raw_entry": entry
                })

        return owned_rawmarks

    def get_item_by_id(self, app_id: str, id_type: IdType = IdType.Steam) -> Item | None:
        try:
            site = SiteManager.get_site_by_id(id_type, app_id)
            if not site:
                raise ValueError(f"{id_type} not in site registry")
            item = site.get_item()
            if not item:
                logger.info(f"fetching game {app_id} from steam")
                site.get_resource_ready()
                item = site.get_item()
        except Exception as e:
            logger.error(f"fetching error: app_id: {app_id}", extra={"exception": e})
            item = None
        return item

    @classmethod
    def estimate_shelf_type(cls, playtime_forever: int, last_played: datetime, app_id: str):
        played_long_enough = playtime_forever / SteamImporter.get_how_long_to_beat(app_id) > .75
        never_played = playtime_forever == 0 and last_played == datetime.fromtimestamp(0)
        playing = datetime.now() - last_played < timedelta(weeks=2)
        # ever played in 2 weeks

        if never_played: return ShelfType.WISHLIST # we all have games purchased and never played...
        elif playing: return ShelfType.PROGRESS
        elif played_long_enough: return ShelfType.COMPLETE
        else: return ShelfType.DROPPED

    # TODO: Implement get_how_long_to_beat:
    # Such data are available in HowLongToBeat.com and igdb, however
    # 1. time_to_beat can be considered a potential metadata of Game item,
    # 2. though sites are primarily used to scrape data, it seems better to extend them as api interface
    # 3. if 1 happens, the time to beat data shall be fetched from Game item, instead of this method
    @classmethod
    def get_how_long_to_beat(cls, steamid: str) -> int:
        return 20
        ...
