import json

from dal import autocomplete
from django import http

from apis_core.apis_entities.models import AbstractEntity


class TeiEntAc(autocomplete.Select2ListView):
    def get(self, request, *args, **kwargs):
        page_size = 200
        offset = (int(self.request.GET.get("page", 1)) - 1) * page_size
        ac_type = self.kwargs["entity"]
        if ac_type == "org":
            ac_type = "institution"
        choices = []
        headers = {"Content-Type": "application/json"}
        ent_model = AbstractEntity.get_entity_class_of_name(ac_type)
        q = self.q.strip()

        res = ent_model.objects.filter(name__startswith=q)
        for r in res[offset : offset + page_size]:
            dates = f"time: {r.start_date} - {r.end_date}"
            f = dict()
            f["id"] = f"{request.build_absolute_uri('/entity/')}{r.pk}"
            if ac_type == "institution":
                f["type"] = "org"
            else:
                f["type"] = f"{ac_type}"
            f["name"] = f"{r!s}"
            f["description"] = f"{dates}"
            choices.append(f)
        return http.HttpResponse(
            json.dumps({"item": choices + [], "pagination": {"more": True}}),
            content_type="application/json",
        )


class TeiCompleterAc(autocomplete.Select2ListView):
    def get(self, request, *args, **kwargs):
        page_size = 200
        offset = (int(self.request.GET.get("page", 1)) - 1) * page_size
        ac_type = self.kwargs["entity"]
        if ac_type == "org":
            ac_type = "institution"
        choices = []
        headers = {"Content-Type": "application/json"}
        ent_model = AbstractEntity.get_entity_class_of_name(ac_type)
        q = self.q.strip()

        res = ent_model.objects.filter(name__startswith=q)
        for r in res[offset : offset + page_size]:
            dates = f"time: {r.start_date} - {r.end_date}"
            f = dict()
            f["tc:value"] = f"{r.uri_set.all()[0]}"
            if ac_type == "institution":
                ent_type = "org"
            else:
                ent_type = f"{ac_type}"
            f["tc:description"] = (
                f"name: {r!s}, type: {ent_type}, dates: {dates}".format(dates)
            )
            choices.append(f)
        return http.HttpResponse(
            json.dumps({"tc:suggestion": choices + [], "pagination": {"more": True}}),
            content_type="application/json",
        )
