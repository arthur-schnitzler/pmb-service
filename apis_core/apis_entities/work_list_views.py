import django_filters
import django_tables2 as tables
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.bootstrap import AccordionGroup
from crispy_bootstrap5.bootstrap5 import BS5Accordion

from dal import autocomplete

from browsing.browsing_utils import GenericListView

from apis_core.apis_entities.models import Work

from apis_core.apis_vocabularies.models import (
    PlaceWorkRelation,
    InstitutionWorkRelation,
    PersonWorkRelation,
    WorkWorkRelation,
)
from apis_core.helper_functions.utils import get_child_classes

excluded_cols = [
    "start_start_date",
    "start_end_date",
    "end_start_date",
    "end_end_date",
    "status",
    "source",
    "references",
    "published",
    "tempentityclass_ptr",
    "review",
]


WORK_PERSON_RELATION_CHOICES = [
    (f"{x.id}", f"{x.label_reverse} (ID: {x.id})") for x in PersonWorkRelation.objects.all()
]
WORK_PLACE_RELATION_CHOICES = [
    (f"{x.id}", f"{x} (ID: {x.id})") for x in PlaceWorkRelation.objects.all()
]
WORK_WORK_RELATION_CHOICES = [
    (f"{x.id}", f"{x} (ID: {x.id})") for x in WorkWorkRelation.objects.all()
]
WORK_INSTITUTION_RELATION_CHOICES = [
    (f"{x.id}", f"{x} (ID: {x.id})") for x in InstitutionWorkRelation.objects.all()
]


class WorkListFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        lookup_expr="icontains",
        label="Werktitel",
        help_text="eingegebene Zeichenkette muss im Titel enthalten sein",
    )
    related_with_person = django_filters.LookupChoiceFilter(
        lookup_choices=WORK_PERSON_RELATION_CHOICES,
        label="Bezugsperson",
        help_text="Name einer Bezugsperson und die Art des Beziehung, z.B. 'Schnitzler' und 'wurde geschaffen von'",
        method="related_person_filter",
    )

    def related_person_filter(self, qs, name, value):
        rels = get_child_classes(
            [
                value.lookup_expr,
            ],
            PersonWorkRelation,
        )
        qs = qs.filter(
            personwork_set__related_person__name__icontains=value.value,
            personwork_set__relation_type__in=rels
        )
        return qs


class WorkFilterFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(WorkFilterFormHelper, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.form_class = "genericFilterForm"
        self.form_method = "GET"
        self.form_tag = False
        self.layout = Layout(
            BS5Accordion(
                AccordionGroup(
                    "Eigenschaften",
                    "name",
                    css_id="more",
                ),
                AccordionGroup(
                    "Beziehungen",
                    "related_with_person",
                    css_id="admin_search",
                ),
            )
        )


class WorkTable(tables.Table):
    id = tables.LinkColumn(verbose_name="ID")

    class Meta:
        model = Work
        sequence = ("id", "name", "start_date")
        attrs = {"class": "table table-responsive table-hover"}


class WorkListView(GenericListView):
    model = Work
    filter_class = WorkListFilter
    formhelper_class = WorkFilterFormHelper
    table_class = WorkTable
    init_columns = [
        "id",
        "name",
        "first_name",
        "uris",
        "start_date",
        "end_date",
    ]
    exclude_columns = excluded_cols
    enable_merge = False
    template_name = "apis_entities/list_views/person_list.html"
