from django.conf.urls import url

from . import views

app_name = 'apis_metainfo'

urlpatterns = [
    url(
        r'^apis/metainfo/uri/$',
        views.UriListView.as_view(),
        name='uri_browse'
    ),
    url(
        r'^uri/detail/<int:pk>$',
        views.UriDetailView.as_view(),
        name='uri_detail'
    ),
    url(
        r'^uri/create/$',
        views.UriCreate.as_view(),
        name='uri_create'
    ),
    url(
        r'^uri/edit/<int:pk>$',
        views.UriUpdate.as_view(),
        name='uri_edit'
    ),
    url(
        r'^uri/delete/<int:pk>$',
        views.UriDelete.as_view(),
        name='uri_delete'),
]
