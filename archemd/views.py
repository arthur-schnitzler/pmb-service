from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseNotFound

from apis_core.utils import get_object_from_pk_or_uri

from .arche_md_utils import ArcheMd


def entity_as_arche(request, pk):
    res = get_object_from_pk_or_uri(pk)
    try:
        res = ArcheMd(res.id)
    except ObjectDoesNotExist:
        return HttpResponseNotFound()
    return HttpResponse(res.return_graph().serialize(), content_type="text/turtle")
