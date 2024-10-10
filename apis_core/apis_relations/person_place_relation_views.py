from django import forms
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy

from browsing.browsing_utils import GenericListView, BaseCreateView
from dal import autocomplete
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from django_filters import FilterSet, ModelMultipleChoiceFilter, RangeFilter
import django_tables2 as tables

from apis_core.apis_entities.models import Person, Place
from apis_core.apis_vocabularies.models import PersonPlaceRelation

from .models import PersonPlace
from .config import FIELDS_TO_EXCLUDE


class PersonPlaceForm(forms.ModelForm):

    class Meta:
        model = PersonPlace
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
            "related_place": autocomplete.ModelSelect2(
                url=reverse_lazy(
                    "apis:apis_entities:generic_entities_autocomplete",
                    kwargs={"entity": "place"},
                ),
                attrs={"data-html": True},
            ),
        }

    def __init__(self, *args, **kwargs):
        super(PersonPlaceForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.fields["related_person"].required = True
        self.fields["related_place"].required = True
        self.fields["relation_type"].required = True
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-md-3"
        self.helper.field_class = "col-md-9"
        self.helper.add_input(
            Submit("submit", "save"),
        )


class PersonPlaceCreate(BaseCreateView):

    model = PersonPlace
    form_class = PersonPlaceForm
    success_url = PersonPlace.get_listview_url()

    def get_success_url(self):
        related_person = self.object.related_person
        return f"{self.model.get_listview_url()}?related_person={related_person.id}&sort=-id"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PersonPlaceCreate, self).dispatch(*args, **kwargs)


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
            attrs={"data-html": True},
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
            attrs={"data-html": True},
        ),
    )
    relation_type = ModelMultipleChoiceFilter(
        queryset=PersonPlaceRelation.objects.all().order_by("name"),
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
        model = PersonPlace
        fields = [
            "related_person",
            "related_place",
            "relation_type",
            "start_date__year",
            "end_date__year",
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
            "start_date__year",
            "end_date__year",
        )


class PersonPlaceTable(tables.Table):
    related_person = tables.TemplateColumn(
        """<a href="{{ record.related_person.get_absolute_url }}">{{ record.related_person }}</a>""",
        verbose_name="Person",
    )
    related_place = tables.TemplateColumn(
        """<a href="{{ record.related_place.get_absolute_url }}">{{ record.related_place }}</a>""",
        verbose_name="Ort",
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
        "start_date_written",
        "end_date_written",
        "related_person",
        "relation_type",
        "related_place",
    ]
    verbose_name = "Personen und Orte"
    exclude_columns = FIELDS_TO_EXCLUDE
    enable_merge = False
    template_name = "apis_relations/list_view.html"
