import django_filters
import django_tables2 as tables
from crispy_bootstrap5.bootstrap5 import BS5Accordion
from crispy_forms.bootstrap import AccordionGroup
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from dal import autocomplete

from apis_core.apis_entities.models import Work
from apis_core.apis_entities.base_filter import MyBaseFilter
from apis_core.apis_vocabularies.models import (
    InstitutionWorkRelation,
    PersonWorkRelation,
    PlaceWorkRelation,
    WorkType,
    WorkWorkRelation,
)
from apis_core.helper_functions.utils import get_child_classes
from browsing.browsing_utils import GenericListView

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
    (f"{x.id}", f"{x.label_reverse} (ID: {x.id})")
    for x in PersonWorkRelation.objects.all()
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


class WorkListFilter(MyBaseFilter):
    name = django_filters.CharFilter(
        lookup_expr="icontains",
        label="Werktitel",
        help_text="eingegebene Zeichenkette muss im Titel enthalten sein",
    )
    year_of_creation = django_filters.NumberFilter(
        field_name="start_date__year", label="Schöpfungsdatum", help_text="z.B. 1880"
    )
    related_with_person = django_filters.LookupChoiceFilter(
        lookup_choices=WORK_PERSON_RELATION_CHOICES,
        label="Bezugsperson",
        help_text="Name einer Bezugsperson und die Art des Beziehung, z.B. 'Schnitzler' und 'wurde geschaffen von'",
        method="related_person_filter",
    )
    related_with_work = django_filters.LookupChoiceFilter(
        lookup_choices=WORK_WORK_RELATION_CHOICES,
        label="Werk",
        help_text="Name einer Werkes und die Art des Beziehung, z.B. 'Schnitzler' und 'wurde geschaffen von'",
        method="related_work_filter",
    )
    kind = django_filters.ModelMultipleChoiceFilter(
        queryset=WorkType.objects.all(),
        help_text="Art/Typ des Werkes, z.B. 'Roman'",
        label="Werktype",
        widget=autocomplete.Select2Multiple(
            url="/apis/vocabularies/autocomplete/worktype/normal/",
        ),
    )

    def related_work_filter(self, qs, name, value):
        rels = get_child_classes(
            [
                value.lookup_expr,
            ],
            WorkWorkRelation,
        )
        qs = qs.filter(
            workb_set__name__icontains=value.value, workb_relationtype_set__in=rels
        )
        return qs

    def related_person_filter(self, qs, name, value):
        rels = get_child_classes(
            [
                value.lookup_expr,
            ],
            PersonWorkRelation,
        )
        qs = qs.filter(
            personwork_set__related_person__name__icontains=value.value,
            personwork_set__relation_type__in=rels,
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
                    "kind",
                    "year_of_creation",
                    css_id="more",
                ),
                AccordionGroup(
                    "Beziehungen",
                    "related_with_person",
                    "related_with_work",
                    css_id="admin_search",
                ),
            )
        )


class WorkTable(tables.Table):
    id = tables.LinkColumn(verbose_name="ID")
    name = tables.columns.Column(verbose_name="Titel")
    label_set = tables.ManyToManyColumn(verbose_name="Labels")
    personwork_set = tables.ManyToManyColumn(
        verbose_name="AutorIn",
        transform=lambda x: x.related_person,
        filter=lambda qs: qs.filter(
            relation_type__in=get_child_classes(
                [
                    1049,
                ],
                PersonWorkRelation,
            )
        ),  # ToDo: don't hardcode the realtion type id here
    )

    class Meta:
        model = Work
        sequence = ("id", "name", "personwork_set", "start_date")
        attrs = {"class": "table table-responsive table-hover"}


class WorkListView(GenericListView):
    model = Work
    filter_class = WorkListFilter
    formhelper_class = WorkFilterFormHelper
    table_class = WorkTable
    init_columns = [
        "id",
        "name",
        "start_date",
        "personwork_set",
        "kind",
    ]
    exclude_columns = excluded_cols
    enable_merge = False
    template_name = "apis_entities/list_view.html"
    verbose_name = "Werke"
    help_text = "Werke help text"
    icon = "bi bi-book apis-work big-icons"
