from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apis_core.apis_entities.api_views import GetEntityGeneric


urlpatterns = [
    path("apis/", include("apis_core.urls", namespace="apis")),
    path("entity/<int:pk>/", GetEntityGeneric.as_view(), name="GetEntityGenericRoot"),
    path("admin/", admin.site.urls),
    path("arche/", include("archemd.urls")),
    path("", include("dumper.urls", namespace="dumper")),
    path("browsing", include("browsing.urls", namespace="browsing")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
