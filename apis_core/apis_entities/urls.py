from django.urls import path

from . import detail_views, views
from .autocomplete3 import GenericEntitiesAutocomplete
from .list_view_event import EventListView
from .list_view_institution import InstitutionListView
from .list_view_person import PersonListView
from .list_view_place import PlaceListView
from .list_view_work import WorkListView

app_name = "apis_entities"

urlpatterns = [
    path(
        "entity/<entity>/<int:pk>/edit",
        views.GenericEntitiesEditView.as_view(),
        name="generic_entities_edit_view",
    ),
    path(
        "entity/<entity>/<int:pk>/detail",
        detail_views.GenericEntitiesDetailView.as_view(),
        name="generic_entities_detail_view",
    ),
    path(
        "entity/<entity>/create",
        views.GenericEntitiesCreateView.as_view(),
        name="generic_entities_create_view",
    ),
    path(
        "entity/<entity>/<int:pk>/delete",
        views.GenericEntitiesDeleteView.as_view(),
        name="generic_entities_delete_view",
    ),
    path(
        "entity/person/list/",
        PersonListView.as_view(),
        name="person_list_view",
    ),
    path(
        "entity/place/list/",
        PlaceListView.as_view(),
        name="place_list_view",
    ),
    path(
        "entity/work/list/",
        WorkListView.as_view(),
        name="work_list_view",
    ),
    path(
        "entity/institution/list/",
        InstitutionListView.as_view(),
        name="institution_list_view",
    ),
    path(
        "entity/event/list/",
        EventListView.as_view(),
        name="event_list_view",
    ),
    path(
        "merge/<entity>/<int:ent_merge_pk>/",
        views.MergeEntitiesView.as_view(),
        name="merge_view",
    ),
    path(
        "autocomplete/<entity>/<int:ent_merge_pk>/",
        GenericEntitiesAutocomplete.as_view(),
        name="generic_entities_autocomplete",
    ),
    path(
        "autocomplete/<entity>/",
        GenericEntitiesAutocomplete.as_view(),
        name="generic_entities_autocomplete",
    ),
    path(
        "autocomplete/<entity>/<db_include>/",
        GenericEntitiesAutocomplete.as_view(),
        name="generic_entities_autocomplete",
    ),
]
