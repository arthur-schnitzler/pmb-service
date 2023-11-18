import django_filters
from django.conf import settings

from dal import autocomplete

from browsing.browsing_utils import GenericListView

from apis_core.apis_entities.models import Person
from apis_core.apis_vocabularies.models import ProfessionType, PersonPlaceRelation
from apis_core.apis_entities.tables import PersonTable
from apis_core.apis_entities.forms import GenericFilterFormHelper

birth_rel = PersonPlaceRelation.objects.filter(name="geboren in")
death_rel = PersonPlaceRelation.objects.filter(name="gestorben in")


def birth_place_filter(qs, name, value):
    rels = birth_rel
    qs = qs.filter(
        personplace_set__related_place__name__icontains=value,
        personplace_set__relation_type__in=rels,
    )
    return qs


def death_place_filter(qs, name, value):
    rels = death_rel
    qs = qs.filter(
        personplace_set__related_place__name__icontains=value,
        personplace_set__relation_type__in=rels,
    )
    return qs


class PersonListFilter(django_filters.FilterSet):
    gender = django_filters.ChoiceFilter(
        choices=(("", "egal"), ("male", "männlich"), ("female", "weiblich"))
    )
    birth_year = django_filters.NumberFilter(
        field_name="start_date__year", label="Geburtsjahr", help_text="z.B. 1880"
    )
    birth_place = django_filters.CharFilter(
        label="Geburtsort",
        method=birth_place_filter,
    )
    death_year = django_filters.NumberFilter(
        field_name="end_date__year", label="Todesjahr", help_text="z.B. 1955"
    )
    death_place = django_filters.CharFilter(
        label="Sterbeort",
        method=death_place_filter,
    )
    first_name = django_filters.CharFilter(
        lookup_expr="icontains",
        label="Vorname",
        help_text="eingegebene Zeichenkette muss im Vornamen enthalten sein",
    )
    profession = django_filters.ModelMultipleChoiceFilter(
        queryset=ProfessionType.objects.all(),
        help_text=Person._meta.get_field("profession").help_text,
        label=Person._meta.get_field("profession").verbose_name,
        widget=autocomplete.Select2Multiple(
            url="/apis/vocabularies/autocomplete/professiontype/normal/",
        ),
    )

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
