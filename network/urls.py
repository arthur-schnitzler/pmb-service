from django.urls import path

from network.views import (
    CalenderView,
    EdgeListViews,
    MapView,
    NetworkView,
    edges_as_calender,
    edges_as_geojson,
    get_realtions_as_tei,
    network_data,
)

app_name = "network"
urlpatterns = [
    path("edges/", EdgeListViews.as_view(), name="edges_browse"),
    path("network-data/", network_data, name="data"),
    path("network/", NetworkView.as_view(), name="network"),
    path("geojson-data/", edges_as_geojson, name="geojson"),
    path("calender-data/", edges_as_calender, name="calender_data"),
    path("calender/", CalenderView.as_view(), name="calender"),
    path("map/", MapView.as_view(), name="map"),
    path("tei/", get_realtions_as_tei, name="tei"),
]
