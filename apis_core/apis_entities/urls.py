from django.urls import path

from . import views, views2, detail_views, merge_views
from .autocomplete3 import (
    GenericEntitiesAutocomplete,
    GenericNetworkEntitiesAutocomplete,
)

from .views2 import GenericEntitiesCreateStanbolView
from .person_list_views import PersonListView
from .work_list_views import WorkListView

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
        name="generic_entities_list",
    ),
    path(
        "entity/work/list/",
        WorkListView.as_view(),
        name="generic_entities_list",
    ),
    path(
        "entity/<entity>/list/",
        views.GenericListViewNew.as_view(),
        name="generic_entities_list",
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
    path(
        "autocomplete-network/<entity>/",
        GenericNetworkEntitiesAutocomplete.as_view(),
        name="generic_network_entities_autocomplete",
    ),
    # TODO __sresch__ : This seems unused. Remove it once sure
    # url(r'^detail/work/<int:pk>',
    #     detail_views.WorkDetailView.as_view(), name='work_detail'),
    path("place/geojson/", views.getGeoJson, name="getGeoJson"),
    path("place/geojson/list/", views.getGeoJsonList, name="getGeoJsonList"),
    path("place/network/list/", views.getNetJsonList, name="getNetJsonList"),
    path(
        "resolve/place/<int:pk>/<uri>",
        views.resolve_ambigue_place,
        name="resolve_ambigue_place",
    ),
    path("maps/birthdeath/", views.birth_death_map, name="birth_death_map"),
    path("networks/relation_place/", views.pers_place_netw, name="pers_place_netw"),
    path("networks/relation_institution/", views.pers_inst_netw, name="pers_inst_netw"),
    path("networks/generic/", views.generic_network_viz, name="generic_network_viz"),
    #    url(
    #        r'^compare/(?P<app>[a-z_]+)/(?P<kind>[a-z]+)/(?P<pk>\d+)', ReversionCompareView.as_view()
    #    ),
    path("merge-objects/", merge_views.merge_objects, name="merge_objects"),
]
