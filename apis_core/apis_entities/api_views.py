from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from rest_framework.decorators import api_view
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.settings import api_settings

from apis_core.apis_metainfo.models import TempEntityClass, Uri
from .api_renderers import (
    EntityToTEI,
)


class GetEntityGeneric(GenericAPIView):
    queryset = TempEntityClass.objects.all()
    renderer_classes = tuple(api_settings.DEFAULT_RENDERER_CLASSES) + (EntityToTEI,)
    if getattr(settings, "APIS_RENDERERS", None) is not None:
        rend_add = tuple()
        for rd in settings.APIS_RENDERERS:
            rend_mod = __import__(rd)
            for name, cls in rend_mod.__dict__.items():
                rend_add + (cls,)
        renderer_classes += rend_add

    def get_object(self, pk, request):
        try:
            return TempEntityClass.objects_inheritance.get_subclass(pk=pk)
        except TempEntityClass.DoesNotExist:
            uri2 = Uri.objects.filter(uri=request.build_absolute_uri())
            if uri2.count() == 1:
                return TempEntityClass.objects_inheritance.get_subclass(
                    pk=uri2[0].entity_id
                )
            else:
                raise Http404

    def get(self, request, pk):
        ent = self.get_object(pk, request)
        data_view = request.GET.get("data-view", False)
        format_param = request.GET.get("format", False)
        requested_format = request.META.get("HTTP_ACCEPT")
        if requested_format is not None:
            if (
                requested_format.startswith("text/html")
                and not data_view
                and not format_param
            ):
                return redirect(ent)
        res = EntitySerializer(ent, context={"request": request})
        return Response(res.data)


@api_view(["GET"])
def uri_resolver(request):
    uri = request.query_params.get("uri", None)
    f = request.query_params.get("target_format", "gui")
    if uri is None:
        raise Http404
    else:
        uri = Uri.objects.get(uri=uri)
        if f == "gui":
            ent = TempEntityClass.objects_inheritance.get_subclass(pk=uri.entity_id)
            c_name = ent.__class__.__name__
            url = reverse(
                "apis_core:apis_entities:generic_entities_detail_view",
                kwargs={"pk": uri.entity_id, "entity": c_name.lower()},
            )
        else:
            url = reverse(
                "apis_core:apis_api2:GetEntityGeneric", kwargs={"pk": uri.entity_id}
            ) + "?format={}".format(f)
        return redirect(url)
