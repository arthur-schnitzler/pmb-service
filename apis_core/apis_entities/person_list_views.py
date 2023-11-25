import django_filters
import django_tables2 as tables
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.bootstrap import AccordionGroup
from crispy_bootstrap5.bootstrap5 import BS5Accordion

from dal import autocomplete

from browsing.browsing_utils import GenericListView

from apis_core.apis_entities.models import Person
from apis_core.apis_vocabularies.models import ProfessionType

from apis_core.apis_vocabularies.models import (
    PersonPersonRelation,
    PersonPlaceRelation,
    PersonWorkRelation,
    PersonInstitutionRelation,
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

PERSON_PERSON_RELATION_CHOICES = [
    (f"{x.id}", f"{x} (ID: {x.id})") for x in PersonPersonRelation.objects.all()
]
PERSON_PLACE_RELATION_CHOICES = [
    (f"{x.id}", f"{x} (ID: {x.id})") for x in PersonPlaceRelation.objects.all()
]
PERSON_WORK_RELATION_CHOICES = [
    (f"{x.id}", f"{x} (ID: {x.id})") for x in PersonWorkRelation.objects.all()
]
PERSON_INSTITUTION_RELATION_CHOICES = [
    (f"{x.id}", f"{x} (ID: {x.id})") for x in PersonInstitutionRelation.objects.all()
]


class PersonListFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        lookup_expr="icontains",
        label="Nachname",
        help_text="eingegebene Zeichenkette muss im Nachnamen enthalten sein",
    )
    gender = django_filters.ChoiceFilter(
        choices=(("", "egal"), ("male", "männlich"), ("female", "weiblich"))
    )
    birth_year = django_filters.NumberFilter(
        field_name="start_date__year", label="Geburtsjahr", help_text="z.B. 1880"
    )
    death_year = django_filters.NumberFilter(
        field_name="end_date__year", label="Todesjahr", help_text="z.B. 1955"
    )
    first_name = django_filters.CharFilter(
        lookup_expr="icontains",
        label="Vorname",
        help_text="eingegebene Zeichenkette muss im Vornamen enthalten sein",
    )
    profession = django_filters.ModelMultipleChoiceFilter(
        queryset=ProfessionType.objects.all(),
        help_text="Beruf/Profession der Person, z.B. 'Kritiker'",
        label="Beruf/Profession",
        widget=autocomplete.Select2Multiple(
            url="/apis/vocabularies/autocomplete/professiontype/normal/",
        ),
    )
    related_with_person = django_filters.LookupChoiceFilter(
        lookup_choices=PERSON_PERSON_RELATION_CHOICES,
        label="Bezugsperson",
        help_text="Name einer Bezugsperson und die Art des Beziehung, z.B. 'Schnitzler' und 'arbeitet für'",
        method="related_person_filter",
    )
    related_with_place = django_filters.LookupChoiceFilter(
        lookup_choices=PERSON_PLACE_RELATION_CHOICES,
        label="Bezugsort",
        help_text="Name eines Ortes und die Art des Beziehung, z.B. 'Linz' und 'beerdigt in'",
        method="related_place_filter",
    )
    related_with_work = django_filters.LookupChoiceFilter(
        lookup_choices=PERSON_WORK_RELATION_CHOICES,
        label="Werk",
        help_text="Name eines Werkes und die Art des Beziehung, z.B. 'Reigen' und 'hat geschaffen'",
        method="related_work_filter",
    )
    related_with_institution = django_filters.LookupChoiceFilter(
        lookup_choices=PERSON_INSTITUTION_RELATION_CHOICES,
        label="Institution",
        help_text="Name einer Institution und die Art des Beziehung, z.B. 'Znanie' und 'besitzt'",
        method="related_institution_filter",
    )

    def related_institution_filter(self, qs, name, value):
        rels = get_child_classes(
            [
                value.lookup_expr,
            ],
            PersonInstitutionRelation,
        )
        qs = qs.filter(
            personinstitution_set__related_institution__name__icontains=value.value,
            personinstitution_set__relation_type__in=rels,
        )
        return qs

    def related_work_filter(self, qs, name, value):
        rels = get_child_classes(
            [
                value.lookup_expr,
            ],
            PersonWorkRelation,
        )
        qs = qs.filter(
            personwork_set__related_work__name__icontains=value.value,
            personwork_set__relation_type__in=rels,
        )
        return qs

    def related_place_filter(self, qs, name, value):
        rels = get_child_classes(
            [
                value.lookup_expr,
            ],
            PersonPlaceRelation,
        )
        qs = qs.filter(
            personplace_set__related_place__name__icontains=value.value,
            personplace_set__relation_type__in=rels,
        )
        return qs

    def related_person_filter(self, qs, name, value):
        rels = get_child_classes(
            [
                value.lookup_expr,
            ],
            PersonPersonRelation,
        )
        qs = qs.filter(
            personb_set__name__icontains=value.value, personb_relationtype_set__in=rels
        )
        return qs

    class Meta:
        model = Person
        fields = [
            "name",
            "first_name",
        ]


class PersonFilterFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(PersonFilterFormHelper, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.form_class = "genericFilterForm"
        self.form_method = "GET"
        self.form_tag = False
        self.layout = Layout(
            BS5Accordion(
                AccordionGroup(
                    "Eigenschaften",
                    "name",
                    "first_name",
                    "profession",
                    "gender",
                    "birth_year",
                    "death_year",
                    css_id="more",
                ),
                AccordionGroup(
                    "Beziehungen",
                    "related_with_person",
                    "related_with_place",
                    "related_with_work",
                    "related_with_institution",
                    css_id="admin_search",
                ),
            )
        )


class PersonTable(tables.Table):
    id = tables.LinkColumn(verbose_name="ID")

    class Meta:
        model = Person
        sequence = ("id", "name", "first_name")
        attrs = {"class": "table table-responsive table-hover"}


class PersonListView(GenericListView):
    model = Person
    filter_class = PersonListFilter
    formhelper_class = PersonFilterFormHelper
    table_class = PersonTable
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
    template_name = "apis_entities/list_views/list.html"
