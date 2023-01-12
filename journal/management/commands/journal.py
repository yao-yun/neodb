from django.core.management.base import BaseCommand
import pprint
from journal.models import *
from journal.importers.douban import DoubanImporter
from users.models import User


class Command(BaseCommand):
    help = "journal app utilities"

    def add_arguments(self, parser):
        parser.add_argument(
            "--cleanup",
            action="store_true",
            help="purge invalid data (visibility=99)",
        )
        parser.add_argument(
            "--douban-import-redo",
            action="store",
            help="reimport for user id",
        )
        parser.add_argument(
            "--douban-import-reset",
            action="store",
            help="reset for user id",
        )

    def handle(self, *args, **options):
        if options["cleanup"]:
            for pcls in [Content, ListMember]:
                for cls in pcls.__subclasses__():
                    self.stdout.write(f"Cleaning up {cls}...")
                    cls.objects.filter(visibility=99).delete()

        if options["douban_import_redo"]:
            user = User.objects.get(pk=options["douban_import_redo"])
            self.stdout.write(f"Redo import for {user}...")
            DoubanImporter.redo(user)

        if options["douban_import_reset"]:
            user = User.objects.get(pk=options["douban_import_reset"])
            self.stdout.write(f"Reset import for {user}...")
            DoubanImporter.reset(user)

        self.stdout.write(self.style.SUCCESS(f"Done."))
