from .forms import GndForm
from django.views.generic.edit import FormView
from django.urls import reverse
from apis_core.apis_entities.models import Person, Uri
from django.core.exceptions import ObjectDoesNotExist
from pylobid.pylobid import PyLobidPerson
from AcdhArcheAssets.uri_norm_rules import get_normalized_uri
from acdh_id_reconciler import gnd_to_wikidata


class GndFormView(FormView):
    template_name = "normdata/create_from_gnd.html"
    form_class = GndForm

    def get_success_url(self):
        return reverse("apis:apis_entities:person_list_view")

    def form_valid(self, form):
        raw_gnd_url = form.data["gnd_url"]
        gnd_id = get_normalized_uri(raw_gnd_url)
        try:
            Uri.objects.get(uri=gnd_id)
            return super().form_valid(form)
        except ObjectDoesNotExist:
            pass
        try:
            wikidata_id = gnd_to_wikidata(gnd_id)["wikidata"]
        except (IndexError, KeyError):
            wikidata_id = False
        if wikidata_id:
            try:
                Uri.objects.get(uri=get_normalized_uri(wikidata_id))
                return super().form_valid(form)
            except ObjectDoesNotExist:
                person = Person.objects.create(name=wikidata_id)
                Uri.objects.create(
                    uri=get_normalized_uri(wikidata_id),
                    domain="wikidata",
                    entity=person,
                )
                Uri.objects.create(uri=gnd_id, domain="gnd", entity=person)
            return super().form_valid(form)
        else:
            py_ent = PyLobidPerson(gnd_id, fetch_related=False)
            person_dict = {}
            if ", " in py_ent.pref_name:
                person_dict["name"], person_dict["first_name"] = py_ent.pref_name.split(
                    ", "
                )
            else:
                person_dict["name"] = py_ent.pref_name
            person = Person.objects.create(**person_dict)
            Uri.objects.create(uri=gnd_id, domain="gnd", entity=person)
            return super().form_valid(form)
