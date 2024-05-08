from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404

from django.shortcuts import get_object_or_404

from apis_core.apis_metainfo.models import TempEntityClass, Uri


def get_object_from_pk_or_uri(pk):
    """checks if the given pk exists, if not checks if a matching apis-default uri exists
    and returns its entity"""
    try:
        instance = TempEntityClass.objects_inheritance.select_subclasses(
            "place", "person", "work", "event", "institution"
        ).get(pk=pk)
        return instance
    except ObjectDoesNotExist:
        domain = "https://pmb.acdh.oeaw.ac.at/"
        new_uri = f"{domain}entity/{pk}/"
        uri2 = Uri.objects.filter(uri=new_uri)
        if uri2.count() == 1:
            instance = TempEntityClass.objects_inheritance.select_subclasses(
                "place", "person", "work", "event", "institution"
            ).get(pk=uri2[0].entity_id)
        elif uri2.count() == 0:
            temp_obj = get_object_or_404(Uri, uri=new_uri[:-1])
            instance = TempEntityClass.objects_inheritance.select_subclasses(
                "place", "person", "work", "event", "institution"
            ).get(pk=temp_obj.entity_id)
        else:
            raise Http404
        return instance
