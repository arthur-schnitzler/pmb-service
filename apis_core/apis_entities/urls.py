from django.urls import path

from . import views, views2, detail_views, merge_views
from .autocomplete3 import (
    GenericEntitiesAutocomplete,
    GenericNetworkEntitiesAutocomplete,
)

from .views2 import GenericEntitiesCreateStanbolView

app_name = "apis_entities"

urlpatterns = [
    path(
        "entity/(?P<entity>[a-z]+)/<int:pk>/edit",
        views2.GenericEntitiesEditView.as_view(),
        name="generic_entities_edit_view",
    ),
    path(
        "entity/(?P<entity>[a-z]+)/<int:pk>/detail",
        detail_views.GenericEntitiesDetailView.as_view(),
        name="generic_entities_detail_view",
    ),
    path(
        "entity/(?P<entity>[a-z]+)/create",
        views2.GenericEntitiesCreateView.as_view(),
        name="generic_entities_create_view",
    ),
    path(
        "entity/(?P<entity>[a-z]+)/<int:pk>/delete",
        views2.GenericEntitiesDeleteView.as_view(),
        name="generic_entities_delete_view",
    ),
    path(
        "entity/(?P<entity>[a-z]+)/list/",
        views.GenericListViewNew.as_view(),
        name="generic_entities_list",
    ),
    path(
        "autocomplete/createstanbol/(?P<entity>[a-zA-Z0-9-]+)/",
        GenericEntitiesCreateStanbolView.as_view(),
        name="generic_entities_stanbol_create",
    ),
    path(
        "autocomplete/createstanbol/(?P<entity>[a-zA-Z0-9-]+)/(?P<ent_merge_pk>[0-9]+)/",
        GenericEntitiesCreateStanbolView.as_view(),
        name="generic_entities_stanbol_create",
    ),
    path(
        "autocomplete/(?P<entity>[a-zA-Z0-9-]+)/(?P<ent_merge_pk>[0-9]+)/",
        GenericEntitiesAutocomplete.as_view(),
        name="generic_entities_autocomplete",
    ),
    path(
        "autocomplete/(?P<entity>[a-zA-Z0-9-]+)/",
        GenericEntitiesAutocomplete.as_view(),
        name="generic_entities_autocomplete",
    ),
    path(
        "autocomplete/(?P<entity>[a-zA-Z0-9-]+)/(?P<db_include>[a-z]+)/",
        GenericEntitiesAutocomplete.as_view(),
        name="generic_entities_autocomplete",
    ),
    path(
        "autocomplete-network/(?P<entity>[a-zA-Z0-9-]+)/",
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
        "resolve/place/<int:pk>/(?P<uri>.+)",
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
