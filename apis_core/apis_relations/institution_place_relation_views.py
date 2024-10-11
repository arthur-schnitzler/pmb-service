from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from browsing.browsing_utils import GenericListView, BaseCreateView, BaseUpdateView

from apis_core.apis_vocabularies.models import InstitutionPlaceRelation
from apis_core.apis_relations.models import InstitutionPlace
from apis_core.apis_relations.config import FIELDS_TO_EXCLUDE
from apis_core.apis_relations.utils import (
    generate_relation_form,
    generate_relation_filter_formhelper,
    generate_relation_filter,
    generate_relation_table,
)


class InstitutionPlaceCreate(BaseCreateView):

    model = InstitutionPlace
    form_class = generate_relation_form(InstitutionPlace)

    def get_success_url(self):
        return self.object.get_object_list_view()

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(InstitutionPlaceCreate, self).dispatch(*args, **kwargs)


class InstitutionPlaceUpdate(BaseUpdateView):

    model = InstitutionPlace
    form_class = generate_relation_form(InstitutionPlace)

    def get_success_url(self):
        return self.object.get_object_list_view()

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(InstitutionPlaceUpdate, self).dispatch(*args, **kwargs)


class InstitutionPlaceListView(GenericListView):
    model = InstitutionPlace
    filter_class = generate_relation_filter(InstitutionPlace, InstitutionPlaceRelation)
    formhelper_class = generate_relation_filter_formhelper()
    table_class = generate_relation_table(InstitutionPlace)
    init_columns = [
        "start_date_written",
        "end_date_written",
        "source",
        "relation_type",
        "target",
        "crud",
    ]
    verbose_name = "Institutionen und Orte"
    exclude_columns = FIELDS_TO_EXCLUDE
    enable_merge = False
    template_name = "apis_relations/list_view.html"
