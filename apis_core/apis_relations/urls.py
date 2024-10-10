from django.urls import path

from . import views
from . import person_place_relation_views
from . import person_work_relation_views
from . import person_person_relation_views
from .views import copy_relation


app_name = "apis_relations"

urlpatterns = [
    path(
        "copy/<relation_class>/<int:pk>",
        copy_relation,
        name="copy_relation",
    ),
    path(
        "person-place/",
        person_place_relation_views.PersonPlaceListView.as_view(),
        name="personplace",
    ),
    path(
        "person-place/create/",
        person_place_relation_views.PersonPlaceCreate.as_view(),
        name="personplace_create",
    ),
    path(
        "person-place/edit/<int:pk>",
        person_place_relation_views.PersonPlaceUpdate.as_view(),
        name="personplace_edit",
    ),
    path(
        "person-work/",
        person_work_relation_views.PersonWorkListView.as_view(),
        name="personwork",
    ),
    path(
        "person-work/create/",
        person_work_relation_views.PersonWorkCreate.as_view(),
        name="personwork_create",
    ),
    path(
        "person-work/edit/<int:pk>",
        person_work_relation_views.PersonWorkUpdate.as_view(),
        name="personwork_edit",
    ),
    path(
        "person-person/",
        person_person_relation_views.PersonPersonListView.as_view(),
        name="personperson",
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
