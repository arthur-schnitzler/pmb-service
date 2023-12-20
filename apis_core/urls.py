import os
from django.urls import path
from django.conf.urls import include
from rest_framework import routers

from apis_core.api_routers import views

from apis_core.apis_vocabularies.api_views import UserViewSet
from apis_core.helper_functions.ContentType import GetContentTypes
from apis_core.apis_metainfo.views import beacon

app_name = "apis_core"

router = routers.DefaultRouter()
for app_label, model_str in GetContentTypes().get_names():
    if "_" in app_label:
        route_prefix = app_label.split("_")[1]
    else:
        route_prefix = app_label
    try:
        router.register(
            "{}/{}".format(route_prefix, model_str.lower()),
            views[model_str.lower()],
            model_str.lower(),
        )
    except Exception as e:
        print(f"Error: {e}{model_str.lower()} not found, skipping")
        print(f"{model_str.lower()} not found, skipping")


router.register("users", UserViewSet)

if os.environ.get("NEW_PMB"):
    urlpatterns = [
        path("beacon/", beacon, name="beacon"),
    ]
else:
    urlpatterns = [
        path("beacon/", beacon, name="beacon"),
        path("labels/", include("apis_core.apis_labels.urls", namespace="apis_labels")),
        path("tei/", include("apis_core.apis_tei.tei_urls", namespace="apis_tei")),
        path(
            "entities/", include("apis_core.apis_entities.urls", namespace="apis_entities")
        ),
        path("openrefine/", include("apis_core.openrefine.urls", namespace="openrefine")),
        path(
            "relations/",
            include("apis_core.apis_relations.urls", namespace="apis_relations"),
        ),
        path(
            "vocabularies/",
            include("apis_core.apis_vocabularies.urls", namespace="apis_vocabularies"),
        ),
        path(
            "metainfo/",
            include("apis_core.apis_metainfo.urls", namespace="apis_metainfo"),
        ),
        path(
            "metainfo-ac/",
            include("apis_core.apis_metainfo.dal_urls", namespace="apis_metainfo-ac"),
        ),
    ]
