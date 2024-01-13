import django_filters
import django_tables2 as tables
from crispy_bootstrap5.bootstrap5 import BS5Accordion
from crispy_forms.bootstrap import AccordionGroup
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from dal import autocomplete

from apis_core.apis_entities.models import Place
from apis_core.apis_entities.base_filter import MyBaseFilter
from apis_core.apis_vocabularies.models import (
    PersonPlaceRelation,
    PlaceType,
    PlaceWorkRelation,
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


PLACE_PERSON_RELATION_CHOICES = [
    (f"{x.id}", f"{x.label_reverse} (ID: {x.id})")
    for x in PersonPlaceRelation.objects.all()
]
PLACE_WORK_RELATION_CHOICES = [
    (f"{x.id}", f"{x} (ID: {x.id})") for x in PlaceWorkRelation.objects.all()
]


class PlaceListFilter(MyBaseFilter):
    name = django_filters.CharFilter(
        method="name_label_filter",
        label="Ortsname",
        help_text="eingegebene Zeichenkette muss im Ortsnamen oder in einem der Labels enthalten sein",
    )
    related_with_person = django_filters.LookupChoiceFilter(
        lookup_choices=PLACE_PERSON_RELATION_CHOICES,
        label="Bezugsperson",
        help_text="Name einer Bezugsperson und die Art des Beziehung, z.B. 'Schnitzler' und 'wurde geboren in'",
        method="related_person_filter",
    )
    related_with_work = django_filters.LookupChoiceFilter(
        lookup_choices=PLACE_WORK_RELATION_CHOICES,
        label="Werk",
        help_text="Name einer Werkes und die Art des Beziehung, z.B. 'Schnitzler' und 'wurde geschaffen von'",
        method="related_work_filter",
    )
    kind = django_filters.ModelMultipleChoiceFilter(
        queryset=PlaceType.objects.all(),
        help_text="Art/Typ des Ortes, z.B. 'Roman'",
        label="Ortstyp",
        widget=autocomplete.Select2Multiple(
            url="/apis/vocabularies/autocomplete/placetype/normal/",
        ),
    )

    def related_work_filter(self, qs, name, value):
        rels = get_child_classes(
            [
                value.lookup_expr,
            ],
            PlaceWorkRelation,
        )
        qs = qs.filter(
            placework_set__related_work__name__icontains=value.value,
            placework_set__relation_type__in=rels,
        )
        return qs

    def related_person_filter(self, qs, name, value):
        rels = get_child_classes(
            [
                value.lookup_expr,
            ],
            PersonPlaceRelation,
        )
        qs = qs.filter(
            personplace_set__related_person__name__icontains=value.value,
            personplace_set__relation_type__in=rels,
        )
        return qs


class PlaceFilterFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(PlaceFilterFormHelper, self).__init__(*args, **kwargs)
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


class PlaceTable(tables.Table):
    id = tables.LinkColumn(verbose_name="ID")
    name = tables.columns.Column(verbose_name="Titel")
    label_set = tables.ManyToManyColumn(verbose_name="Labels")

    class Meta:
        model = Place
        sequence = ("id", "name", "start_date")
        attrs = {"class": "table table-responsive table-hover"}


class PlaceListView(GenericListView):
    model = Place
    filter_class = PlaceListFilter
    formhelper_class = PlaceFilterFormHelper
    table_class = PlaceTable
    init_columns = [
        "id",
        "name",
        "kind",
    ]
    exclude_columns = excluded_cols
    enable_merge = False
    template_name = "apis_entities/list_view.html"
    verbose_name = "Orte"
    help_text = "Orte help text"
