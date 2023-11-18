from django.urls import path

from apis_core.apis_entities.autocomplete3 import GenericVocabulariesAutocomplete
from apis_core.apis_vocabularies import views

app_name = "apis_vocabularies"

urlpatterns = [
    path("download/<model_name>/", views.dl_vocabs_as_csv, name="dl-vocabs"),
    path(
        "autocomplete/<vocab>/<direct>/",
        GenericVocabulariesAutocomplete.as_view(),
        name="generic_vocabularies_autocomplete",
    ),
]
