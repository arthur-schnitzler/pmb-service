from django.urls import path

from . import rel_views
from . import views

app_name = "apis_relations"

urlpatterns = [
    path("ajax/get/", views.get_form_ajax, name="get_form_ajax"),
    path("ajax/save/<entity_type>/<kind_form>/<int:SiteID>/<int:ObjectID>/",
        views.save_ajax_form,
        name="save_ajax_form",
    ),
    path("<entity>/list/",
        rel_views.GenericRelationView.as_view(),
        name="generic_relations_list",
    ),
    path("<entity>/<int:pk>/detail",
        rel_views.GenericRelationDetailView.as_view(),
        name="generic_relations_detail_view",
    ),
]
