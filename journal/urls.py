from django.urls import path, re_path
from .views import *
from catalog.models import *


app_name = 'journal'


def _get_all_categories():
    res = "|".join(CATEGORY_LIST.keys())
    return res


def _get_all_shelf_types():
    return "|".join(ShelfType.values)


urlpatterns = [
    path('wish/<str:item_uuid>', wish, name='wish'),
    path('like/<str:piece_uuid>', like, name='like'),
    path('mark/<str:item_uuid>', mark, name='mark'),
    path('add_to_collection/<str:item_uuid>', add_to_collection, name='add_to_collection'),

    path('review/<str:review_uuid>', review_retrieve, name='review_retrieve'),
    path('review/create/<str:item_uuid>/', review_edit, name='review_create'),
    path('review/edit/<str:item_uuid>/<str:review_uuid>', review_edit, name='review_edit'),
    path('review/delete/<str:review_uuid>', review_delete, name='review_delete'),

    path('collection/<str:collection_uuid>', collection_retrieve, name='collection_retrieve'),
    path('collection/create/', collection_edit, name='collection_create'),
    path('collection/edit/<str:collection_uuid>', collection_edit, name='collection_edit'),
    path('collection/delete/<str:collection_uuid>', collection_delete, name='collection_delete'),
    path('collection/<str:collection_uuid>/items', collection_retrieve_items, name='collection_retrieve_items'),
    path('collection/<str:collection_uuid>/append_item', collection_append_item, name='collection_append_item'),
    path('collection/<str:collection_uuid>/delete_item/<str:collection_member_uuid>', collection_delete_item, name='collection_delete_item'),
    path('collection/<str:collection_uuid>/move_up_item/<str:collection_member_uuid>', collection_move_up_item, name='collection_move_up_item'),
    path('collection/<str:collection_uuid>/move_down_item/<str:collection_member_uuid>', collection_move_down_item, name='collection_move_down_item'),
    path('collection/<str:collection_uuid>/update_item_note/<str:collection_member_uuid>', collection_update_item_note, name='collection_update_item_note'),

    re_path(r'^user/(?P<user_name>[A-Za-z0-9_\-.@]+)/(?P<shelf_type>' + _get_all_shelf_types() + ')/(?P<item_category>' + _get_all_categories() + ')/$', user_mark_list, name='user_mark_list'),
    re_path(r'^user/(?P<user_name>[A-Za-z0-9_\-.@]+)/reviews/(?P<item_category>' + _get_all_categories() + ')/$', user_review_list, name='user_review_list'),
    re_path(r'^user/(?P<user_name>[A-Za-z0-9_\-.@]+)/tags/(?P<tag_title>[^/]+)/$', user_tag_member_list, name='user_tag_member_list'),
    re_path(r'^user/(?P<user_name>[A-Za-z0-9_\-.@]+)/collections/$', user_collection_list, name='user_collection_list'),
    re_path(r'^user/(?P<user_name>[A-Za-z0-9_\-.@]+)/like/collections/$', user_liked_collection_list, name='user_liked_collection_list'),
    re_path(r'^user/(?P<user_name>[A-Za-z0-9_\-.@]+)/tags/$', user_tag_list, name='user_tag_list'),

    re_path(r'^user/(?P<user_name>[A-Za-z0-9_\-.@]+)/$', home, name='user_profile'),

]
