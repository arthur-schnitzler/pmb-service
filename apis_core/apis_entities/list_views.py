import django_filters
from dal import autocomplete

from browsing.browsing_utils import GenericListView

from apis_core.apis_entities.models import Person
from apis_core.apis_vocabularies.models import ProfessionType
from apis_core.apis_relations.models import PersonPlace
from apis_core.apis_entities.tables import PersonTable
from apis_core.apis_entities.forms import GenericFilterFormHelper



class PersonListFilter(django_filters.FilterSet):
    gender = django_filters.ChoiceFilter(
        choices=(("", "egal"), ("male", "männlich"), ("female", "weiblich"))
    )
    birth_year = django_filters.NumberFilter(
        field_name="start_date__year", label="Geburtsjahr", help_text="z.B. 1880"
    )
    death_year = django_filters.NumberFilter(
        field_name="start_date__year", label="Todesjahr", help_text="z.B. 1955"
    )
    first_name = django_filters.CharFilter(
        lookup_expr="icontains", label="Vorname", help_text="eingegebene Zeichenkette muss im Vornamen enthalten sein"
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
