import json
import pandas as pd
from typing import Any
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404, JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView


from browsing.browsing_utils import BaseCreateView, BaseUpdateView

from .forms import UriForm
from .models import Uri

PROJECT_NAME = settings.PROJECT_NAME


def beacon(request):
    domain = request.build_absolute_uri("/")
    result = f"#FORMAT: BEACON\n#NAME: {PROJECT_NAME}\n"
    uris = [
        (x.uri, x.entity.name, x.entity.id)
        for x in Uri.objects.filter(uri__icontains="d-nb.info/gnd")
    ]
    for x in uris:
        result = result + f"{x[0]}|" f"{x[1]}|" f"{domain}entity/{x[2]}/\n"
    return HttpResponse(result, content_type="text/plain")


def wikidata_beacon(request):
    domain = request.build_absolute_uri("/")
    result = f"#FORMAT: BEACON\n#NAME: {PROJECT_NAME}\n"
    uris = [
        (x.uri, x.entity.name, x.entity.id)
        for x in Uri.objects.filter(uri__icontains="wikidata.org/entity/")
    ]
    for x in uris:
        result = result + f"{x[0]}|" f"{x[1]}|" f"{domain}entity/{x[2]}/\n"
    return HttpResponse(result, content_type="text/plain")


def domain_uris(request, domain):
    df = pd.DataFrame(
        list(
            Uri.objects.filter(domain__icontains=domain).values(
                "uri", "entity_id", "entity__name"
            )
        )
    )
    if df.empty:
        raise Http404
    df["entity_id"] = df.apply(
        lambda x: f"https://pmb.acdh.oeaw.ac.at/entity/{x['entity_id']}", axis=1
    )
    format = request.GET.get("format", "csv")
    if format not in ["csv", "json"]:
        format = "csv"
    if format == "csv":
        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{domain}.csv"'},
        )
        df.to_csv(response, index=False)
    else:
        df = df.set_index("uri")
        out = df.to_json(orient="index")
        response = JsonResponse(json.loads(out))
    return response


class UriDetailView(DetailView):
    model = Uri
    template_name = "apis_metainfo/uri_detail.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["entity_type"] = "uri"
        print(context["object"].get_icon())
        context["icon"] = context["object"].get_icon()
        return context


class UriCreate(BaseCreateView):
    model = Uri
    form_class = UriForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UriCreate, self).dispatch(*args, **kwargs)


class UriUpdate(BaseUpdateView):
    model = Uri
    form_class = UriForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UriUpdate, self).dispatch(*args, **kwargs)


class UriDelete(DeleteView):
    model = Uri
    template_name = "apis_entities/confirm_delete.html"
    success_url = reverse_lazy("apis_core:apis_metainfo:uri_browse")

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UriDelete, self).dispatch(*args, **kwargs)
