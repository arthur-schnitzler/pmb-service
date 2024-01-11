import django_filters
import django_tables2 as tables
from crispy_bootstrap5.bootstrap5 import BS5Accordion
from crispy_forms.bootstrap import AccordionGroup
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from dal import autocomplete

from apis_core.apis_entities.models import Institution
from apis_core.apis_entities.base_filter import MyBaseFilter
from apis_core.apis_vocabularies.models import (
    InstitutionEventRelation,
    InstitutionInstitutionRelation,
    InstitutionPlaceRelation,
    InstitutionType,
    InstitutionWorkRelation,
    PersonInstitutionRelation,
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
INSTITUTION_EVENT_RELATION_CHOICES = [
    (f"{x.id}", f"{x} (ID: {x.id})") for x in InstitutionEventRelation.objects.all()
]


class InstitutionListFilter(MyBaseFilter):
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
        help_text="Name eines Werkes und die Art des Beziehung, z.B. 'enthält' und 'Armand Carrel'",
        method="related_work_filter",
    )
    related_with_place = django_filters.LookupChoiceFilter(
        lookup_choices=INSTITUTION_PLACE_RELATION_CHOICES,
        label="Ort",
        help_text="Name eines Ortes und die Art des Beziehung, z.B. 'angesiedelt in' und 'Linz'",
        method="related_place_filter",
    )
    related_with_event = django_filters.LookupChoiceFilter(
        lookup_choices=INSTITUTION_EVENT_RELATION_CHOICES,
        label="Ereignis",
        help_text="Name eines Ereignisses  und die Art des Beziehung, z.B. 'veranstaltet' und 'Aufführung'",
        method="related_event_filter",
    )
    kind = django_filters.ModelMultipleChoiceFilter(
        queryset=InstitutionType.objects.all(),
        help_text="Art/Typ der Institution, z.B. 'Roman'",
        label="Institutionstyp",
        widget=autocomplete.Select2Multiple(
            url="/apis/vocabularies/autocomplete/institutiontype/normal/",
        ),
    )

    def related_event_filter(self, qs, name, value):
        rels = get_child_classes(
            [
                value.lookup_expr,
            ],
            InstitutionEventRelation,
        )
        qs = qs.filter(
            institutionevent_set__related_event__name__icontains=value.value,
            institutionevent_set__relation_type__in=rels,
        )
        return qs

    def related_place_filter(self, qs, name, value):
        rels = get_child_classes(
            [
                value.lookup_expr,
            ],
            InstitutionPlaceRelation,
        )
        qs = qs.filter(
            institutionplace_set__related_place__name__icontains=value.value,
            institutionplace_set__relation_type__in=rels,
        )
        return qs

    def related_work_filter(self, qs, name, value):
        rels = get_child_classes(
            [
                value.lookup_expr,
            ],
            InstitutionWorkRelation,
        )
        qs = qs.filter(
            institutionwork_set__related_work__name__icontains=value.value,
            institutionwork_set__relation_type__in=rels,
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
            personinstitution_set__related_person__name__icontains=value.value,
            personinstitution_set__relation_type__in=rels,
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
                    "related_with_place",
                    "related_with_event",
                    "related_with_work",
                    css_id="admin_search",
                ),
            )
        )


class InstitutionTable(tables.Table):
    id = tables.LinkColumn(verbose_name="ID")
    name = tables.columns.Column(verbose_name="Titel")
    label_set = tables.ManyToManyColumn(verbose_name="Labels")
    institutionplace_set = tables.ManyToManyColumn(
        verbose_name="angesiedelt in",
        transform=lambda x: x.related_place,
        filter=lambda qs: qs.filter(
            relation_type__in=get_child_classes(
                [970, 1141, 1160],
                InstitutionPlaceRelation,
            )
        ),  # ToDo: don't hardcode the realtion type id here
    )

    class Meta:
        model = Institution
        sequence = ("id", "name", "institutionplace_set", "start_date")
        attrs = {"class": "table table-responsive table-hover"}


class InstitutionListView(GenericListView):
    model = Institution
    filter_class = InstitutionListFilter
    formhelper_class = InstitutionFilterFormHelper
    table_class = InstitutionTable
    init_columns = [
        "id",
        "name",
        "institutionplace_set",
        "start_date",
        "kind",
    ]
    exclude_columns = excluded_cols
    enable_merge = False
    template_name = "apis_entities/list_view.html"
    verbose_name = "Institution"
    help_text = "Institution help text"
    icon = "bi bi-building-gear apis-institution big-icons"
