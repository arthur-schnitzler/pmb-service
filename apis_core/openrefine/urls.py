from django.urls import path

from . import views

app_name = "openrefine"

urlpatterns = [
    path("reconcile", views.reconcile, name="reconcile"),
    path("properties", views.properties, name="properties"),
    path("suggest/type", views.suggest_types, name="suggest_types"),
]
