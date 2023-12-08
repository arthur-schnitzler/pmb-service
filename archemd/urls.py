from django.urls import path

from .views import entity_as_arche

urlpatterns = [
    path("<int:pk>", entity_as_arche),
]
