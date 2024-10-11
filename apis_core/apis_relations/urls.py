from django.urls import path

from . import views
from . import person_place_relation_views
from . import person_work_relation_views
from . import person_person_relation_views
from . import person_institution_relation_views
from . import person_event_relation_views
from .views import copy_relation


app_name = "apis_relations"

urlpatterns = [
    path(
        "copy/<relation_class>/<int:pk>",
        copy_relation,
        name="copy_relation",
    ),
    path(
        "person-event/",
        person_event_relation_views.PersonEventListView.as_view(),
        name="personevent",
    ),
    path(
        "person-event/create/",
        person_event_relation_views.PersonEventCreate.as_view(),
        name="personevent_create",
    ),
    path(
        "person-event/edit/<int:pk>",
        person_event_relation_views.PersonEventUpdate.as_view(),
        name="personevent_edit",
    ),
    path(
        "person-institution/",
        person_institution_relation_views.PersonInstitutionListView.as_view(),
        name="personinstitution",
    ),
    path(
        "person-institution/create/",
        person_institution_relation_views.PersonInstitutionCreate.as_view(),
        name="personinstitution_create",
    ),
    path(
        "person-institution/edit/<int:pk>",
        person_institution_relation_views.PersonInstitutionUpdate.as_view(),
        name="personinstitution_edit",
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
        "person-person/create/",
        person_person_relation_views.PersonPersonCreate.as_view(),
        name="personperson_create",
    ),
    path(
        "person-person/edit/<int:pk>",
        person_person_relation_views.PersonPersonUpdate.as_view(),
        name="personperson_edit",
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
