from django.urls import path

from . import views
from . import person_place_relation_views
from . import person_work_relation_views
from . import person_person_relation_views

app_name = "apis_relations"

urlpatterns = [
    path(
        "person-place/",
        person_place_relation_views.PersonPlaceListView.as_view(),
        name="person_place",
    ),
    path(
        "person-work/",
        person_work_relation_views.PersonWorkListView.as_view(),
        name="person_work",
    ),
    path(
        "person-person/",
        person_person_relation_views.PersonPersonListView.as_view(),
        name="person_person",
    ),
    path(
        "delete/<int:relation_id>/",
        views.delete_relation_view,
        name="delete_relation",
    ),
    path("ajax/get/", views.get_form_ajax, name="get_form_ajax"),
    path(
        "ajax/save/<entity_type>/<kind_form>/<int:SiteID>/<int:ObjectID>/",
        views.save_ajax_form,
        name="save_ajax_form",
    ),
    path(
        "ajax/save/<entity_type>/<kind_form>/<int:SiteID>/",
        views.save_ajax_form,
        name="save_ajax_form",
    ),
]
