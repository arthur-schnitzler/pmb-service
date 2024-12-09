from django.urls import path
from network.views import EdgeListViews, network_data, NetworkView, edegs_as_geojson


app_name = "network"
urlpatterns = [
    path("edges/", EdgeListViews.as_view(), name="edges_browse"),
    path("network-data/", network_data, name="data"),
    path("network/", NetworkView.as_view(), name="network"),
    path("geojson-data/", edegs_as_geojson, name="network"),
]
