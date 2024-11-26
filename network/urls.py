from django.urls import path
from network.views import EdgeListViews, network_data, NetworkView


app_name = "network"
urlpatterns = [
    path("edges/", EdgeListViews.as_view(), name="edges_browse"),
    path("csv/", network_data, name="data"),
    path("network/", NetworkView.as_view(), name="network"),
]
