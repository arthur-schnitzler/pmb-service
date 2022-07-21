from django.urls import path

from dumper.views import HomePageView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
]
