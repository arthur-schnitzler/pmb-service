from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("apis/", include("apis_core.urls", namespace="apis")),
    path("admin/", admin.site.urls),
    path("arche/", include("archemd.urls")),
    path("", include("dumper.urls", namespace="dumper")),
    path("browsing", include("browsing.urls", namespace="browsing")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
