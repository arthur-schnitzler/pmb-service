from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from browsing.browsing_utils import GenericListView, BaseCreateView, BaseUpdateView

from apis_core.apis_vocabularies.models import PlaceWorkRelation
from apis_core.apis_relations.models import PlaceWork
from apis_core.apis_relations.config import FIELDS_TO_EXCLUDE
from apis_core.apis_relations.utils import (
    generate_relation_form,
    generate_relation_filter_formhelper,
    generate_relation_filter,
    generate_relation_table,
)


class PlaceWorkCreate(BaseCreateView):

    model = PlaceWork
    form_class = generate_relation_form(PlaceWork)

    def get_success_url(self):
        return self.object.get_object_list_view()

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PlaceWorkCreate, self).dispatch(*args, **kwargs)


class PlaceWorkUpdate(BaseUpdateView):

    model = PlaceWork
    form_class = generate_relation_form(PlaceWork)

    def get_success_url(self):
        return self.object.get_object_list_view()

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PlaceWorkUpdate, self).dispatch(*args, **kwargs)


class PlaceWorkListView(GenericListView):
    model = PlaceWork
    filter_class = generate_relation_filter(PlaceWork, PlaceWorkRelation)
    formhelper_class = generate_relation_filter_formhelper()
    table_class = generate_relation_table(PlaceWork)
    init_columns = [
        "start_date_written",
        "end_date_written",
        "source",
        "relation_type",
        "target",
        "crud",
    ]
    verbose_name = "Orte und Werke"
    exclude_columns = FIELDS_TO_EXCLUDE
    enable_merge = False
    template_name = "apis_relations/list_view.html"
