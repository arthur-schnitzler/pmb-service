from django.http import HttpResponseNotFound
from django.shortcuts import redirect
from django.views.generic.edit import FormView

from .forms import NormDataImportForm
from .utils import import_from_normdata


class NormDataImportFormView(FormView):
    template_name = "normdata/create_from_gnd.html"
    form_class = NormDataImportForm

    def form_valid(self, form):
        raw_url = form.data["normdata_url"]
        entity_type = form.data["entity_type"]
        temp_ent = import_from_normdata(raw_url, entity_type)
        if temp_ent is not None:
            entity = temp_ent.get_child_entity()
            redirect_url = entity.get_edit_url()
            return redirect(redirect_url)
        else:
            return HttpResponseNotFound(
                f"<h1>Error</h1><p>Zu <strong>{raw_url}</strong> konnte keine Entität angelegt werden</p>"
            )
