from django.urls import path

from . import views

app_name = "normdata"


urlpatterns = [
    path("import-from-gnd/", views.GndFormView.as_view(), name="import_from_gnd")
]
