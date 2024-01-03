from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apis_core.apis_entities import resolver_views


urlpatterns = [
    path("apis/", include("apis_core.urls", namespace="apis")),
    path("normdata/", include("normdata.urls", namespace="normdata")),
    path("admin/", admin.site.urls),
    path("arche/", include("archemd.urls", namespace="archemd")),
    path("uri/", resolver_views.uri_resolver, name="uri-resolver"),
    path("", include("dumper.urls", namespace="dumper")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
