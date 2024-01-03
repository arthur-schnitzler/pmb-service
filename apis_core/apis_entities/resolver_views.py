from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import redirect

from apis_core.apis_metainfo.models import TempEntityClass, Uri


def uri_resolver(request):
    uri = request.GET.get("uri", None)
    # format_param = request.GET.get("format", False)
    # requested_format = request.META.get("HTTP_ACCEPT")
    if uri is None:
        raise Http404
    else:
        try:
            uri = Uri.objects.get(uri=uri)
        except ObjectDoesNotExist:
            raise Http404
        entity = TempEntityClass.objects_inheritance.get_subclass(pk=uri.entity_id)
        url = entity.get_absolute_url()
        return redirect(url)
