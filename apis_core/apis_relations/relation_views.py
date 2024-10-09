from browsing.browsing_utils import GenericListView
from dal import autocomplete
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django.urls import reverse_lazy
from django_filters import FilterSet, ModelMultipleChoiceFilter
import django_tables2 as tables
from apis_core.apis_entities.models import Person, Place
from .models import PersonPlace


excluded_cols = [
    "start_start_date",
    "start_end_date",
    "end_start_date",
    "end_end_date",
    "status",
    "source",
    "published",
    "tempentityclass_ptr",
    "review",
]


class PersonPlaceFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(PersonPlaceFormHelper, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.form_class = "genericFilterForm"
        self.form_method = "GET"
        self.form_tag = False
        self.layout = Layout(
            "related_person",
            "related_place",
            "relation_type",
        )


class PersonPlaceListFilter(FilterSet):
    related_person = ModelMultipleChoiceFilter(
        queryset=Person.objects.all(),
        help_text="Wähle eine oder mehrere Personen",
        label="Personen",
        widget=autocomplete.Select2Multiple(
            url=reverse_lazy(
                "apis:apis_entities:generic_entities_autocomplete",
                kwargs={"entity": "person"},
            ),
        ),
    )
    related_place = ModelMultipleChoiceFilter(
        queryset=Place.objects.all(),
        help_text="Wähle einen oder mehrere Orte",
        label="Orte",
        widget=autocomplete.Select2Multiple(
            url=reverse_lazy(
                "apis:apis_entities:generic_entities_autocomplete",
                kwargs={"entity": "place"},
            ),
        ),
    )

    class Meta:
        model = PersonPlace
        fields = [
            "related_person",
            "related_place",
            "relation_type",
        ]


class PersonPlaceTable(tables.Table):
    related_person = tables.TemplateColumn(
        "{{ record.related_person }}", verbose_name="Person"
    )
    related_place = tables.TemplateColumn(
        "{{ record.related_place }}", verbose_name="Ort"
    )
    relation_type = tables.TemplateColumn("{{ record.relation_type }}")
    start_date_written = tables.TemplateColumn(
        "{% if record.start_date_written %} {{ record.start_date_written }} {% endif %}",
        verbose_name="Start",
    )
    end_date_written = tables.TemplateColumn(
        "{% if record.end_date_written %} {{ record.end_date_written }} {% endif %}",
        verbose_name="End",
    )

    class Meta:
        model = PersonPlace
        sequence = (
            "id",
            "related_person",
            "relation_type",
            "related_place",
            "start_date_written",
        )


class PersonPlaceListView(GenericListView):
    model = PersonPlace
    filter_class = PersonPlaceListFilter
    formhelper_class = PersonPlaceFormHelper
    table_class = PersonPlaceTable
    init_columns = [
        "id",
        "start_date_written",
        "end_date_written",
        "related_person",
        "relation_type",
        "related_place",
    ]
    verbose_name = "Personen und Orte"
    exclude_columns = excluded_cols
    enable_merge = False
    template_name = "apis_relations/list_view.html"
