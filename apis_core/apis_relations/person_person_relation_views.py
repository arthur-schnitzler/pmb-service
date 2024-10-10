from browsing.browsing_utils import GenericListView
from dal import autocomplete
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django.urls import reverse_lazy
from django_filters import FilterSet, ModelMultipleChoiceFilter, RangeFilter
import django_tables2 as tables

from apis_core.apis_entities.models import Person
from apis_core.apis_vocabularies.models import PersonPersonRelation

from .config import FIELDS_TO_EXCLUDE
from .models import PersonPerson


class PersonPersonListFilter(FilterSet):
    related_persona = ModelMultipleChoiceFilter(
        queryset=Person.objects.all(),
        help_text="Wähle eine oder mehrere Personen",
        label="Personen",
        widget=autocomplete.Select2Multiple(
            url=reverse_lazy(
                "apis:apis_entities:generic_entities_autocomplete",
                kwargs={"entity": "person"},
            ),
            attrs={"data-html": True},
        ),
    )
    related_personb = ModelMultipleChoiceFilter(
        queryset=Person.objects.all(),
        help_text="Wähle einen oder mehrere Persone",
        label="Persone",
        widget=autocomplete.Select2Multiple(
            url=reverse_lazy(
                "apis:apis_entities:generic_entities_autocomplete",
                kwargs={"entity": "person"},
            ),
            attrs={"data-html": True},
        ),
    )
    relation_type = ModelMultipleChoiceFilter(
        queryset=PersonPersonRelation.objects.all().order_by("name"),
        label="Art der Beziehung",
        help_text="Mehrfachauswahl möglich",
    )
    start_date__year = RangeFilter(
        label="Anfang (Jahr)",
    )
    end_date__year = RangeFilter(
        label="Ende (Jahr)",
    )

    class Meta:
        model = PersonPerson
        fields = [
            "related_persona",
            "related_personb",
            "relation_type",
            "start_date__year",
            "end_date__year",
        ]


class PersonPersonFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(PersonPersonFormHelper, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.form_class = "genericFilterForm"
        self.form_method = "GET"
        self.form_tag = False
        self.layout = Layout(
            "related_persona",
            "related_personb",
            "relation_type",
            "start_date__year",
            "end_date__year",
        )


class PersonPersonTable(tables.Table):
    related_persona = tables.TemplateColumn(
        """<a href="{{ record.related_persona.get_absolute_url }}">{{ record.related_persona }}</a>""",
        verbose_name="Person",
    )
    related_personb = tables.TemplateColumn(
        """<a href="{{ record.related_personb.get_absolute_url }}">{{ record.related_personb }}</a>""",
        verbose_name="Person",
    )
    relation_type = tables.TemplateColumn(
        "{{ record.relation_type }}", verbose_name="Art der Beziehung"
    )
    start_date_written = tables.TemplateColumn(
        "{% if record.start_date_written %} {{ record.start_date_written }} {% endif %}",
        verbose_name="Start",
    )
    end_date_written = tables.TemplateColumn(
        "{% if record.end_date_written %} {{ record.end_date_written }} {% endif %}",
        verbose_name="End",
    )

    class Meta:
        model = PersonPerson
        sequence = (
            "id",
            "related_persona",
            "relation_type",
            "related_personb",
            "start_date_written",
        )


class PersonPersonListView(GenericListView):
    model = PersonPerson
    filter_class = PersonPersonListFilter
    formhelper_class = PersonPersonFormHelper
    table_class = PersonPersonTable
    init_columns = [
        "start_date_written",
        "end_date_written",
        "related_persona",
        "relation_type",
        "related_personb",
    ]
    verbose_name = "Personen und Personen"
    exclude_columns = FIELDS_TO_EXCLUDE
    enable_merge = False
    template_name = "apis_relations/list_view.html"
