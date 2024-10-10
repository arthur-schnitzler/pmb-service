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

from apis_core.apis_entities.models import Person, Work
from apis_core.apis_vocabularies.models import PersonWorkRelation

from .models import PersonWork
from .config import FIELDS_TO_EXCLUDE, CRUD_COLUMN


class PersonWorkForm(forms.ModelForm):

    class Meta:
        model = PersonWork
        exclude = FIELDS_TO_EXCLUDE + [
            "collection",
        ]
        widgets = {
            "related_person": autocomplete.ModelSelect2(
                url=reverse_lazy(
                    "apis:apis_entities:generic_entities_autocomplete",
                    kwargs={"entity": "person"},
                ),
                attrs={"data-html": True},
            ),
            "related_work": autocomplete.ModelSelect2(
                url=reverse_lazy(
                    "apis:apis_entities:generic_entities_autocomplete",
                    kwargs={"entity": "work"},
                ),
                attrs={"data-html": True},
            ),
        }

    def __init__(self, *args, **kwargs):
        super(PersonWorkForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.fields["related_person"].required = True
        self.fields["related_work"].required = True
        self.fields["relation_type"].required = True
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-md-3"
        self.helper.field_class = "col-md-9"
        self.helper.add_input(
            Submit("submit", "save"),
        )


class PersonWorkCreate(BaseCreateView):

    model = PersonWork
    form_class = PersonWorkForm

    def get_success_url(self):
        return self.object.get_object_list_view()

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PersonWorkCreate, self).dispatch(*args, **kwargs)


class PersonWorkUpdate(BaseUpdateView):

    model = PersonWork
    form_class = PersonWorkForm

    def get_success_url(self):
        return self.object.get_object_list_view()

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PersonWorkUpdate, self).dispatch(*args, **kwargs)


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
        """
        <a href="{{ record.related_person.get_absolute_url }}">{{ record.related_person }}</a>
        """,
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
    crud = CRUD_COLUMN

    class Meta:
        model = PersonWork
        sequence = (
            "id",
            "related_person",
            "relation_type",
            "related_work",
            "start_date_written",
            "end_date_written",
            "crud",
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
        "crud",
    ]
    verbose_name = "Personen und Werke"
    exclude_columns = FIELDS_TO_EXCLUDE
    enable_merge = False
    template_name = "apis_relations/list_view.html"
