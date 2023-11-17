from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("apis/entities/", include("apis_core.apis_entities.urls")),
    path("admin/", admin.site.urls),
    path("arche/", include("archemd.urls")),
    path("", include("dumper.urls")),
]
