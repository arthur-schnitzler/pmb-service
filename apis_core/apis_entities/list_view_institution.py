import django_filters
import django_tables2 as tables
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.bootstrap import AccordionGroup
from crispy_bootstrap5.bootstrap5 import BS5Accordion

from dal import autocomplete

from browsing.browsing_utils import GenericListView

from apis_core.apis_entities.models import Institution

from apis_core.apis_vocabularies.models import (
    PersonInstitutionRelation,
    InstitutionWorkRelation,
    InstitutionPlaceRelation,
    InstitutionInstitutionRelation,
    InstitutionType,
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


INSTITUTION_PERSON_RELATION_CHOICES = [
    (f"{x.id}", f"{x.label_reverse} (ID: {x.id})")
    for x in PersonInstitutionRelation.objects.all()
]
INSTITUTION_PLACE_RELATION_CHOICES = [
    (f"{x.id}", f"{x} (ID: {x.id})") for x in InstitutionPlaceRelation.objects.all()
]
INSTITUTION_WORK_RELATION_CHOICES = [
    (f"{x.id}", f"{x} (ID: {x.id})") for x in InstitutionWorkRelation.objects.all()
]
INSTITUTION_INSTITUTION_RELATION_CHOICES = [
    (f"{x.id}", f"{x} (ID: {x.id})")
    for x in InstitutionInstitutionRelation.objects.all()
]


class InstitutionListFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        lookup_expr="icontains",
        label="Name der Institution",
        help_text="eingegebene Zeichenkette muss im Titel enthalten sein",
    )
    year_of_creation = django_filters.NumberFilter(
        field_name="start_date__year", label="Gründungsdatum", help_text="z.B. 1880"
    )
    related_with_person = django_filters.LookupChoiceFilter(
        lookup_choices=INSTITUTION_PERSON_RELATION_CHOICES,
        label="Bezugsperson",
        help_text="Name einer Bezugsperson und die Art des Beziehung, z.B. 'Schnitzler' und 'wurde geschaffen von'",
        method="related_person_filter",
    )
    related_with_work = django_filters.LookupChoiceFilter(
        lookup_choices=INSTITUTION_WORK_RELATION_CHOICES,
        label="Werk",
        help_text="Name einer Werkes und die Art des Beziehung, z.B. 'Schnitzler' und 'wurde geschaffen von'",
        method="related_work_filter",
    )
    kind = django_filters.ModelMultipleChoiceFilter(
        queryset=InstitutionType.objects.all(),
        help_text="Art/Typ der Institution, z.B. 'Roman'",
        label="Institutionstyp",
        widget=autocomplete.Select2Multiple(
            url="/apis/vocabularies/autocomplete/institutiontype/normal/",
        ),
    )

    def related_work_filter(self, qs, name, value):
        rels = get_child_classes(
            [
                value.lookup_expr,
            ],
            InstitutionWorkRelation,
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
            PersonInstitutionRelation,
        )
        qs = qs.filter(
            personwork_set__related_person__name__icontains=value.value,
            personwork_set__relation_type__in=rels,
        )
        return qs


class InstitutionFilterFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(InstitutionFilterFormHelper, self).__init__(*args, **kwargs)
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


class InstitutionTable(tables.Table):
    id = tables.LinkColumn(verbose_name="ID")
    name = tables.columns.Column(verbose_name="Titel")
    label_set = tables.ManyToManyColumn(verbose_name="Labels")
    # personwork_set = tables.ManyToManyColumn(
    #     verbose_name="AutorIn",
    #     transform=lambda x: x.related_person,
    #     filter=lambda qs: qs.filter(
    #         relation_type__in=get_child_classes(
    #             [
    #                 1049,
    #             ],
    #             PersonWorkRelation,
    #         )
    #     ),  # ToDo: don't hardcode the realtion type id here
    # )

    class Meta:
        model = Institution
        sequence = ("id", "name", "start_date")
        attrs = {"class": "table table-responsive table-hover"}


class InstitutionListView(GenericListView):
    model = Institution
    filter_class = InstitutionListFilter
    formhelper_class = InstitutionFilterFormHelper
    table_class = InstitutionTable
    init_columns = [
        "id",
        "name",
        "start_date",
        "kind",
    ]
    exclude_columns = excluded_cols
    enable_merge = False
    template_name = "apis_entities/list_views/list.html"
    verbose_name = "Institution"
    help_text = "Institution help text"
    icon = "bi bi-building-gear apis-institution big-icons"
