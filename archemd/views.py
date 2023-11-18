from django.http import HttpResponse, HttpResponseNotFound, Http404
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404

# from apis_core.apis_entities.detail_views import get_object_from_pk_or_uri
from apis_core.apis_metainfo.models import Uri, TempEntityClass
from .arche_md_utils import ArcheMd


# ToDo: remove this function when updating apis-core package
def get_object_from_pk_or_uri(request, pk):
    """checks if the given pk exists, if not checks if a matching apis-default uri exists
    and returns its entity"""
    try:
        instance = TempEntityClass.objects_inheritance.get_subclass(pk=pk)
        return instance
    except TempEntityClass.DoesNotExist:
        domain = "https://pmb.acdh.oeaw.ac.at/"
        new_uri = f"{domain}entity/{pk}/"
        uri2 = Uri.objects.filter(uri=new_uri)
        if uri2.count() == 1:
            instance = TempEntityClass.objects_inheritance.get_subclass(
                pk=uri2[0].entity_id
            )
        elif uri2.count() == 0:
            temp_obj = get_object_or_404(Uri, uri=new_uri[:-1])
            instance = TempEntityClass.objects_inheritance.get_subclass(
                pk=temp_obj.entity_id
            )
        else:
            raise Http404
        return instance


def entity_as_arche(request, pk):
    res = get_object_from_pk_or_uri(request, pk)
    try:
        res = ArcheMd(res.id)
    except ObjectDoesNotExist:
        return HttpResponseNotFound()
    return HttpResponse(res.return_graph().serialize(), content_type="text/turtle")
