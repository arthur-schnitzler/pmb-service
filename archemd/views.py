from django.http import HttpResponse, HttpResponseNotFound
from django.core.exceptions import ObjectDoesNotExist

from .arche_md_utils import ArcheMd


def entity_as_arche(request, pk):
    try:
        res = ArcheMd(pk)
    except ObjectDoesNotExist:
        return HttpResponseNotFound()
    return HttpResponse(res.return_graph().serialize(), content_type="application/x-turtle")
