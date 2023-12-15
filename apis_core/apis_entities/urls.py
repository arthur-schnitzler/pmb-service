from django.urls import path

from . import views2, detail_views, merge_views
from .autocomplete3 import (
    GenericEntitiesAutocomplete,
)

from .views2 import GenericEntitiesCreateStanbolView
from .list_view_person import PersonListView
from .list_view_work import WorkListView
from .list_view_place import PlaceListView
from .list_view_institution import InstitutionListView
from .list_view_event import EventListView


app_name = "apis_entities"

urlpatterns = [
    path(
        "entity/<entity>/<int:pk>/edit",
        views2.GenericEntitiesEditView.as_view(),
        name="generic_entities_edit_view",
    ),
    path(
        "entity/<entity>/<int:pk>/detail",
        detail_views.GenericEntitiesDetailView.as_view(),
        name="generic_entities_detail_view",
    ),
    path(
        "entity/<entity>/create",
        views2.GenericEntitiesCreateView.as_view(),
        name="generic_entities_create_view",
    ),
    path(
        "entity/<entity>/<int:pk>/delete",
        views2.GenericEntitiesDeleteView.as_view(),
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
        "autocomplete/createstanbol/<entity>/",
        GenericEntitiesCreateStanbolView.as_view(),
        name="generic_entities_stanbol_create",
    ),
    path(
        "autocomplete/createstanbol/<entity>/<int:ent_merge_pk>/",
        GenericEntitiesCreateStanbolView.as_view(),
        name="generic_entities_stanbol_create",
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
    path("merge-objects/", merge_views.merge_objects, name="merge_objects"),
]
