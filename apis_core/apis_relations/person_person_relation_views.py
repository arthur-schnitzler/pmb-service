from django import forms
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy

from browsing.browsing_utils import GenericListView, BaseCreateView, BaseUpdateView
from dal import autocomplete
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from django_filters import FilterSet, ModelMultipleChoiceFilter, RangeFilter
import django_tables2 as tables

from apis_core.apis_entities.models import Person
from apis_core.apis_vocabularies.models import PersonPersonRelation

from .models import PersonPerson
from .config import FIELDS_TO_EXCLUDE, CRUD_COLUMN


class PersonPersonForm(forms.ModelForm):

    class Meta:
        model = PersonPerson
        exclude = FIELDS_TO_EXCLUDE + [
            "collection",
        ]
        widgets = {
            "related_persona": autocomplete.ModelSelect2(
                url=reverse_lazy(
                    "apis:apis_entities:generic_entities_autocomplete",
                    kwargs={"entity": "person"},
                ),
                attrs={"data-html": True},
            ),
            "related_personb": autocomplete.ModelSelect2(
                url=reverse_lazy(
                    "apis:apis_entities:generic_entities_autocomplete",
                    kwargs={"entity": "person"},
                ),
                attrs={"data-html": True},
            ),
        }

    def __init__(self, *args, **kwargs):
        super(PersonPersonForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.fields["related_persona"].required = True
        self.fields["related_personb"].required = True
        self.fields["relation_type"].required = True
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-md-3"
        self.helper.field_class = "col-md-9"
        self.helper.add_input(
            Submit("submit", "save"),
        )


class PersonPersonCreate(BaseCreateView):

    model = PersonPerson
    form_class = PersonPersonForm

    def get_success_url(self):
        return self.object.get_object_list_view()

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PersonPersonCreate, self).dispatch(*args, **kwargs)


class PersonPersonUpdate(BaseUpdateView):

    model = PersonPerson
    form_class = PersonPersonForm

    def get_success_url(self):
        return self.object.get_object_list_view()

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PersonPersonUpdate, self).dispatch(*args, **kwargs)


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
        help_text="Wähle einen oder mehrere Personen",
        label="Personen",
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
        """
        <a href="{{ record.related_persona.get_absolute_url }}">{{ record.related_persona }}</a>
        """,
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
    crud = CRUD_COLUMN

    class Meta:
        model = PersonPerson
        sequence = (
            "id",
            "related_persona",
            "relation_type",
            "related_personb",
            "start_date_written",
            "end_date_written",
            "crud",
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
        "crud",
    ]
    verbose_name = "Personen und Personen"
    exclude_columns = FIELDS_TO_EXCLUDE
    enable_merge = False
    template_name = "apis_relations/list_view.html"
