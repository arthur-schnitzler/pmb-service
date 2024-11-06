from django import forms
from django_filters import FilterSet, ModelMultipleChoiceFilter, RangeFilter
from django.urls import reverse_lazy

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from crispy_bootstrap5.bootstrap5 import BS5Accordion
from crispy_forms.bootstrap import AccordionGroup

from dal import autocomplete

import django_tables2 as tables

from apis_core.apis_relations.config import FIELDS_TO_EXCLUDE


def generate_relation_table(MyModelClass):
    ClassA = MyModelClass.get_related_entity_classa()
    ClassB = MyModelClass.get_related_entity_classb()
    class_a_name = ClassA._meta.verbose_name
    class_b_name = ClassB._meta.verbose_name
    source_field = MyModelClass.get_related_entity_field_namea()
    target_field = MyModelClass.get_related_entity_field_nameb()

    class MyTable(tables.Table):
        source = tables.TemplateColumn(
            """
                <a href="{{ record.get_related_entity_instancea.get_absolute_url }}">
                    {{ record.get_related_entity_instancea }}
                </a>
            """,
            accessor=source_field,
            verbose_name=class_a_name,
        )
        target = tables.TemplateColumn(
            """
            <a href="{{ record.get_related_entity_instanceb.get_absolute_url }}">
                {{ record.get_related_entity_instanceb }}
            </a>
            """,
            accessor=target_field,
            verbose_name=class_b_name,
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
        crud = tables.TemplateColumn(
            """
                <a href="{{ record.get_edit_url }}">
                    <i class="bi bi-pencil-square p-1 fs-5" title="Verbindung bearbeiten" aria-hidden="true">
                        <span class="visually-hidden">Verbindung bearbeiten</span>
                    </i>
                </a>
                <a href="{{ record.get_copy_url }}">
                    <i class="bi bi-clipboard p-1 fs-5"></i>
                </a>
                <a href="{{ record.get_delete_url }}">
                    <i class="bi bi-trash p-1 fs-5"></i>
                </a>
            """,
            verbose_name="Ändern, Kopieren oder Löschen",
            orderable=False,
            exclude_from_export=True,
        )

        class Meta:
            model = MyModelClass
            order_by = "-updated"
            sequence = (
                "id",
                "source",
                "relation_type",
                "target",
                "start_date_written",
                "end_date_written",
            )

    return MyTable


def generate_relation_filter(MyModelClass, RelationTypeClass):
    ClassA = MyModelClass.get_related_entity_classa()
    ClassB = MyModelClass.get_related_entity_classb()
    class_a_name = ClassA.__name__
    class_b_name = ClassB.__name__
    class_a_verbose_name = ClassA._meta.verbose_name_plural
    class_b_verbose_name = ClassB._meta.verbose_name_plural
    source_field = MyModelClass.get_related_entity_field_namea()
    target_field = MyModelClass.get_related_entity_field_nameb()

    class MyRelationsListFilter(FilterSet):
        source = ModelMultipleChoiceFilter(
            field_name=source_field,
            queryset=ClassA.objects.all(),
            help_text=f"Wähle eine oder mehrere {class_a_verbose_name}",
            label=class_a_verbose_name,
            widget=autocomplete.Select2Multiple(
                url=reverse_lazy(
                    "apis:apis_entities:generic_entities_autocomplete",
                    kwargs={"entity": class_a_name.lower()},
                ),
                attrs={"data-html": True},
            ),
        )
        target = ModelMultipleChoiceFilter(
            field_name=target_field,
            queryset=ClassB.objects.all(),
            help_text=f"Wähle einen oder mehrere {class_b_verbose_name}",
            label=class_b_verbose_name,
            widget=autocomplete.Select2Multiple(
                url=reverse_lazy(
                    "apis:apis_entities:generic_entities_autocomplete",
                    kwargs={"entity": class_b_name.lower()},
                ),
                attrs={"data-html": True},
            ),
        )
        relation_type = ModelMultipleChoiceFilter(
            queryset=RelationTypeClass.objects.all().order_by("name"),
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
            model = MyModelClass
            fields = [
                source_field,
                target_field,
                "relation_type",
                "start_date__year",
                "end_date__year",
                "collection",
            ]

    return MyRelationsListFilter


def generate_relation_filter_formhelper():

    class MyRelationsFilterFormHelper(FormHelper):
        def __init__(self, *args, **kwargs):
            super(MyRelationsFilterFormHelper, self).__init__(*args, **kwargs)
            self.helper = FormHelper()
            self.form_class = "genericFilterForm"
            self.form_method = "GET"
            self.form_tag = False
            self.layout = Layout(
                "source",
                "target",
                "relation_type",
                "start_date__year",
                "end_date__year",
                "collection",
            )

    return MyRelationsFilterFormHelper


def generate_relation_form(MyModelClass):
    ClassA = MyModelClass.get_related_entity_classa()
    ClassB = MyModelClass.get_related_entity_classb()
    class_a_name = ClassA.__name__
    class_b_name = ClassB.__name__

    class MyForm(forms.ModelForm):

        class Meta:
            model = MyModelClass
            exclude = FIELDS_TO_EXCLUDE + [
                "collection",
            ]
            widgets = {
                MyModelClass.get_related_entity_field_namea(): autocomplete.ModelSelect2(
                    url=reverse_lazy(
                        "apis:apis_entities:generic_entities_autocomplete",
                        kwargs={"entity": f"{class_a_name.lower()}"},
                    ),
                    attrs={"data-html": True},
                ),
                MyModelClass.get_related_entity_field_nameb(): autocomplete.ModelSelect2(
                    url=reverse_lazy(
                        "apis:apis_entities:generic_entities_autocomplete",
                        kwargs={"entity": f"{class_b_name.lower()}"},
                    ),
                    attrs={"data-html": True},
                ),
            }

        def __init__(self, *args, **kwargs):
            super(MyForm, self).__init__(*args, **kwargs)
            self.helper = FormHelper()
            self.helper.form_tag = True
            self.current_model = self._meta.model
            self.fields[
                self.current_model.get_related_entity_field_namea()
            ].required = True
            self.fields["relation_type"].required = True
            self.fields[
                self.current_model.get_related_entity_field_nameb()
            ].required = True
            self.helper.form_class = "form-horizontal"
            self.helper.label_class = "col-md-3"
            self.helper.field_class = "col-md-9"
            self.helper.add_input(
                Submit("submit", "save"),
            )
            self.helper.layout = Layout(
                BS5Accordion(
                    AccordionGroup(
                        "Sehr wichtige Felder",
                        self.current_model.get_related_entity_field_namea(),
                        "relation_type",
                        self.current_model.get_related_entity_field_nameb(),
                        "start_date_written",
                        "end_date_written",
                    ),
                    AccordionGroup(
                        "Notizen und Referenzen",
                        "notes",
                        "references",
                    ),
                    AccordionGroup(
                        "Datumsfelder",
                        "start_date",
                        "end_date",
                    ),
                )
            )

    return MyForm
