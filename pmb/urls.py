from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apis_core.apis_entities import resolver_views
from django.views.generic.base import TemplateView


urlpatterns = (
    [
        path(
            "robots.txt",
            TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        ),
        path("apis/", include("apis_core.urls", namespace="apis")),
        path("normdata/", include("normdata.urls", namespace="normdata")),
        path("admin/", admin.site.urls),
        path("arche/", include("archemd.urls", namespace="archemd")),
        path("uri/", resolver_views.uri_resolver, name="uri-resolver"),
        path(
            "entity/<int:pk>/", resolver_views.entity_resolver, name="entity-resolver"
        ),
        path("", include("dumper.urls", namespace="dumper")),
    ]
    # + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

if settings.DEBUG:
    urlpatterns = urlpatterns + static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
