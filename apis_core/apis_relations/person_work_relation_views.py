from browsing.browsing_utils import GenericListView
from dal import autocomplete
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django.urls import reverse_lazy
from django_filters import FilterSet, ModelMultipleChoiceFilter, RangeFilter
import django_tables2 as tables

from apis_core.apis_entities.models import Person, Work
from apis_core.apis_vocabularies.models import PersonWorkRelation

from .config import FIELDS_TO_EXCLUDE
from .models import PersonWork


class PersonWorkListFilter(FilterSet):
    related_person = ModelMultipleChoiceFilter(
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
    related_work = ModelMultipleChoiceFilter(
        queryset=Work.objects.all(),
        help_text="Wähle einen oder mehrere Werke",
        label="Werke",
        widget=autocomplete.Select2Multiple(
            url=reverse_lazy(
                "apis:apis_entities:generic_entities_autocomplete",
                kwargs={"entity": "work"},
            ),
            attrs={"data-html": True},
        ),
    )
    relation_type = ModelMultipleChoiceFilter(
        queryset=PersonWorkRelation.objects.all().order_by("name"),
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
        model = PersonWork
        fields = [
            "related_person",
            "related_work",
            "relation_type",
            "start_date__year",
            "end_date__year",
        ]


class PersonWorkFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(PersonWorkFormHelper, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.form_class = "genericFilterForm"
        self.form_method = "GET"
        self.form_tag = False
        self.layout = Layout(
            "related_person",
            "related_work",
            "relation_type",
            "start_date__year",
            "end_date__year",
        )


class PersonWorkTable(tables.Table):
    related_person = tables.TemplateColumn(
        """<a href="{{ record.related_person.get_absolute_url }}">{{ record.related_person }}</a>""",
        verbose_name="Person",
    )
    related_work = tables.TemplateColumn(
        """<a href="{{ record.related_work.get_absolute_url }}">{{ record.related_work }}</a>""",
        verbose_name="Werk",
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
        model = PersonWork
        sequence = (
            "id",
            "related_person",
            "relation_type",
            "related_work",
            "start_date_written",
        )


class PersonWorkListView(GenericListView):
    model = PersonWork
    filter_class = PersonWorkListFilter
    formhelper_class = PersonWorkFormHelper
    table_class = PersonWorkTable
    init_columns = [
        "start_date_written",
        "end_date_written",
        "related_person",
        "relation_type",
        "related_work",
    ]
    verbose_name = "Personen und Werke"
    exclude_columns = FIELDS_TO_EXCLUDE
    enable_merge = False
    template_name = "apis_relations/list_view.html"
