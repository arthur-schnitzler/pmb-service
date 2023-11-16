from django.urls import path

from . import rel_views
from . import views

app_name = "apis_relations"

urlpatterns = [
    path("ajax/get/$", views.get_form_ajax, name="get_form_ajax"),
    path("ajax/save/(?P<entity_type>\w+)/(?P<kind_form>\w+)/(?P<SiteID>[0-9]+)(?:/(?P<ObjectID>[0-9]*))?/$",
        views.save_ajax_form,
        name="save_ajax_form",
    ),
    path("(?P<entity>[a-z]+)/list/$",
        rel_views.GenericRelationView.as_view(),
        name="generic_relations_list",
    ),
    path("(?P<entity>[a-z]+)/<int:pk>/detail$",
        rel_views.GenericRelationDetailView.as_view(),
        name="generic_relations_detail_view",
    ),
]
