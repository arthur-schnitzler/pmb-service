from django.urls import path

from .views import entity_as_arche

app_name = "archemd"

urlpatterns = [
    path("<int:pk>", entity_as_arche, name="arche"),
]
