from django.urls import path

from . import views

app_name = "normdata"


urlpatterns = [
    path(
        "import-from-normdata/",
        views.NormDataImportFormView.as_view(),
        name="import_from_normdata",
    )
]
