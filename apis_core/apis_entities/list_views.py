import django_filters
from dal import autocomplete

from browsing.browsing_utils import GenericListView

from apis_core.apis_entities.models import Person
from apis_core.apis_vocabularies.models import ProfessionType
from apis_core.apis_entities.tables import PersonTable
from apis_core.apis_entities.forms import GenericFilterFormHelper
from apis_core.apis_vocabularies.models import PersonPersonRelation, PersonPlaceRelation
from apis_core.helper_functions.utils import get_child_classes

PERSON_PERSON_RELATION_CHOICES = [
    (f"{x.id}", f"{x} (ID: {x.id})") for x in PersonPersonRelation.objects.all()
]
PERSON_PLACE_RELATION_CHOICES = [
    (f"{x.id}", f"{x} (ID: {x.id})") for x in PersonPlaceRelation.objects.all()
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


class PersonListView(GenericListView):
    model = Person
    filter_class = PersonListFilter
    formhelper_class = GenericFilterFormHelper
    table_class = PersonTable
    init_columns = [
        "id",
        "name",
        "start_date",
        "end_date",
    ]
    exclude_columns = []
    enable_merge = False
    template_name = "apis_entities/list_views/person_list.html"
