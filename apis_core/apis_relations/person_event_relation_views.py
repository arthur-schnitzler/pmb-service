from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from browsing.browsing_utils import GenericListView, BaseCreateView, BaseUpdateView

from apis_core.apis_vocabularies.models import PersonEventRelation
from apis_core.apis_relations.models import PersonEvent
from apis_core.apis_relations.config import FIELDS_TO_EXCLUDE
from apis_core.apis_relations.utils import (
    generate_relation_form,
    generate_relation_filter_formhelper,
    generate_relation_filter,
    generate_relation_table,
)


class PersonEventCreate(BaseCreateView):

    model = PersonEvent
    form_class = generate_relation_form(PersonEvent)

    def get_success_url(self):
        return self.object.get_object_list_view()

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PersonEventCreate, self).dispatch(*args, **kwargs)


class PersonEventUpdate(BaseUpdateView):

    model = PersonEvent
    form_class = generate_relation_form(PersonEvent)

    def get_success_url(self):
        return self.object.get_object_list_view()

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PersonEventUpdate, self).dispatch(*args, **kwargs)


class PersonEventListView(GenericListView):
    model = PersonEvent
    filter_class = generate_relation_filter(PersonEvent, PersonEventRelation)
    formhelper_class = generate_relation_filter_formhelper()
    table_class = generate_relation_table(PersonEvent)
    init_columns = [
        "start_date_written",
        "end_date_written",
        "source",
        "relation_type",
        "target",
        "crud",
    ]
    verbose_name = "Personen und Ereignisse"
    exclude_columns = FIELDS_TO_EXCLUDE
    enable_merge = False
    template_name = "apis_relations/list_view.html"
