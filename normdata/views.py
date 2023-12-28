from django.urls import reverse
from django.views.generic.edit import FormView
from icecream import ic

from .forms import GndForm
from .utils import import_from_normdata


class GndFormView(FormView):
    template_name = "normdata/create_from_gnd.html"
    form_class = GndForm

    def get_success_url(self):
        return reverse("apis:apis_entities:person_list_view")

    def form_valid(self, form):
        ic(form.data)
        raw_url = form.data["gnd_url"]
        entity_type = form.data["entity_type"]
        entity = import_from_normdata(raw_url, entity_type)
        ic(entity)
        return super().form_valid(form)
