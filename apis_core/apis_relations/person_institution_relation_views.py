from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from browsing.browsing_utils import GenericListView, BaseCreateView, BaseUpdateView

from apis_core.apis_vocabularies.models import PersonInstitutionRelation
from apis_core.apis_relations.models import PersonInstitution
from apis_core.apis_relations.config import FIELDS_TO_EXCLUDE
from apis_core.apis_relations.utils import (
    generate_relation_form,
    generate_relation_filter_formhelper,
    generate_relation_filter,
    generate_relation_table,
)


class PersonInstitutionCreate(BaseCreateView):

    model = PersonInstitution
    form_class = generate_relation_form(PersonInstitution)

    def get_success_url(self):
        return self.object.get_object_list_view()

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PersonInstitutionCreate, self).dispatch(*args, **kwargs)


class PersonInstitutionUpdate(BaseUpdateView):

    model = PersonInstitution
    form_class = generate_relation_form(PersonInstitution)

    def get_success_url(self):
        return self.object.get_object_list_view()

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PersonInstitutionUpdate, self).dispatch(*args, **kwargs)


class PersonInstitutionListView(GenericListView):
    model = PersonInstitution
    filter_class = generate_relation_filter(
        PersonInstitution, PersonInstitutionRelation
    )
    formhelper_class = generate_relation_filter_formhelper()
    table_class = generate_relation_table(PersonInstitution)
    init_columns = [
        "start_date_written",
        "end_date_written",
        "source",
        "relation_type",
        "target",
        "crud",
    ]
    verbose_name = "Personen und Orte"
    exclude_columns = FIELDS_TO_EXCLUDE
    enable_merge = False
    template_name = "apis_relations/list_view.html"
