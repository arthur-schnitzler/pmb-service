from django.urls import reverse
from django.views.generic.edit import FormView

from .forms import NormDataImportForm
from .utils import import_from_normdata


class NormDataImportFormView(FormView):
    template_name = "normdata/create_from_gnd.html"
    form_class = NormDataImportForm

    def get_success_url(self):
        return reverse("apis:apis_entities:person_list_view")

    def form_valid(self, form):
        raw_url = form.data["normdata_url"]
        entity_type = form.data["entity_type"]
        import_from_normdata(raw_url, entity_type)
        return super().form_valid(form)
