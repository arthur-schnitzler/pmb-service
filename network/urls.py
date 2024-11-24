from django.urls import path
from network.views import EdgeListViews


app_name = "network"
urlpatterns = [
    path("edges/", EdgeListViews.as_view(), name="edges_browse"),
]
