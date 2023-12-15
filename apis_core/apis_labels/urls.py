# -*- coding: utf-8 -*-
from django.urls import path

from . import views

app_name = "apis_labels"

urlpatterns = [
    path("delete-from-tabel/<int:label_id>/", views.delete_label, name="label_delete"),
]
