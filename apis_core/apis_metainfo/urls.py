from django.urls import path

from apis_core.apis_entities.list_view_uris import UriListView
from . import views

app_name = "apis_metainfo"

urlpatterns = [
    path("apis/metainfo/uri/", UriListView.as_view(), name="uri_browse"),
    path("uri/detail/<int:pk>", views.UriDetailView.as_view(), name="uri_detail"),
    path("uri/create/", views.UriCreate.as_view(), name="uri_create"),
    path("uri/edit/<int:pk>", views.UriUpdate.as_view(), name="uri_edit"),
    path("uri/delete/<int:pk>", views.UriDelete.as_view(), name="uri_delete"),
    path("projects/<int:pk>", views.CollectionDetailView.as_view(), name="collection_detail"),
    path("projects/", views.CollectionListView.as_view(), name="collection_browse"),
]
