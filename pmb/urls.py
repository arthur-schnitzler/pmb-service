from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("apis/", include("apis_core.urls", namespace="apis")),
    path("admin/", admin.site.urls),
    path("arche/", include("archemd.urls")),
    path("", include("dumper.urls")),
]
