# -*- coding: utf-8 -*-
from crispy_forms.bootstrap import Accordion, AccordionGroup
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, Layout, Submit
from dal import autocomplete
from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.forms import ModelChoiceField, ModelMultipleChoiceField
from django.urls import reverse

from apis_core.apis_metainfo.models import Collection
from apis_core.helper_functions import DateParser

from .fields import ListSelect2, Select2Multiple
from .models import AbstractEntity


class MergeForm(forms.Form):
    def save(self, *args, **kwargs):
        return self.entity

    def __init__(self, entity, *args, **kwargs):
        attrs = {
            "data-placeholder": "Tippe um Vorschläge zu bekommen",
            "data-minimum-input-length": 1,
            "data-html": True,
            "style": "width: auto",
        }
        ent_merge_pk = kwargs.pop("ent_merge_pk", False)
        super(MergeForm, self).__init__(*args, **kwargs)
        self.entity = entity
        self.helper = FormHelper()
        form_kwargs = {"entity": entity}
        url = reverse(
            "apis:apis_entities:generic_entities_autocomplete",
            args=[entity.title(), "remove"],
        )
        label = "Create {} from reference resources".format(entity.title())
        button_label = "Create"
        if ent_merge_pk:
            form_kwargs["ent_merge_pk"] = ent_merge_pk
            url = reverse(
                "apis:apis_entities:generic_entities_autocomplete",
                args=[entity.title(), ent_merge_pk],
            )
            label = f"Suche nach Objekten vom Type: {entity.title()}"
            button_label = "zusammenführen"
        self.helper.form_action = reverse(
            "apis:apis_entities:merge_view", kwargs=form_kwargs
        )
        self.helper.add_input(Submit("submit", button_label))
        self.fields["entity"] = autocomplete.Select2ListCreateChoiceField(
            label=label,
            widget=ListSelect2(url=url, attrs=attrs),
            # validators=[URLValidator],
        )


def get_entities_form(entity):
    # TODO __sresch__ : consider moving this class outside of the function call to avoid redundant class definitions
    class GenericEntitiesForm(forms.ModelForm):
        class Meta:
            model = AbstractEntity.get_entity_class_of_name(entity)

            exclude = [
                "start_date",
                "start_start_date",
                "start_end_date",
                "start_date_is_exact",
                "end_date",
                "end_start_date",
                "end_end_date",
                "end_date_is_exact",
                "text",
                "source",
                "published",
            ]
            exclude.extend(model.get_related_entity_field_names())
            exclude.extend(model.get_related_relationtype_field_names())

        def __init__(self, *args, **kwargs):
            super(GenericEntitiesForm, self).__init__(*args, **kwargs)
            self.helper = FormHelper()
            self.helper.form_class = entity.title() + "Form"
            self.helper.form_tag = False
            self.helper.help_text_inline = True
            acc_grp1 = Fieldset("Metadata {}".format(entity.title()))
            acc_grp2 = AccordionGroup("MetaInfo", "references", "notes", "review")
            attrs = {
                "data-placeholder": "Tippe um Vorschläge zu bekommen",
                "data-minimum-input-length": 1,
                "data-html": True,
            }

            # list to catch all fields that will not be inserted into accordion group acc_grp2
            fields_list_unsorted = []

            for f in self.fields.keys():
                if isinstance(
                    self.fields[f], (ModelMultipleChoiceField, ModelChoiceField)
                ):
                    v_name_p = str(self.fields[f].queryset.model.__name__)
                    if isinstance(self.fields[f], ModelMultipleChoiceField):
                        widget1 = Select2Multiple
                    else:
                        widget1 = ListSelect2
                    if (
                        ContentType.objects.get(
                            app_label__in=[
                                "apis_entities",
                                "apis_metainfo",
                                "apis_relations",
                                "apis_vocabularies",
                                "apis_labels",
                            ],
                            model=v_name_p.lower(),
                        ).app_label.lower()
                        == "apis_vocabularies"
                    ):
                        self.fields[f].widget = widget1(
                            url=reverse(
                                "apis:apis_vocabularies:generic_vocabularies_autocomplete",
                                kwargs={"vocab": v_name_p.lower(), "direct": "normal"},
                            ),
                            attrs=attrs,
                        )
                        if self.instance:
                            res = []
                            if isinstance(self.fields[f], ModelMultipleChoiceField):
                                try:
                                    for x in getattr(self.instance, f).all():
                                        res.append((x.pk, x.label))
                                except ValueError:
                                    pass
                                self.fields[f].initial = res
                                self.fields[f].choices = res
                            else:
                                try:
                                    res = getattr(self.instance, f)
                                    if res is not None:
                                        self.fields[f].initial = (res.pk, res.label)
                                        self.fields[f].choices = [
                                            (res.pk, res.label),
                                        ]
                                except ValueError:
                                    res = ""
                if f not in acc_grp2:
                    # append to unsorted list, so that it can be sorted and
                    # afterwards attached to accordion group acc_grp1
                    fields_list_unsorted.append(f)

            def sort_fields_list(list_unsorted, entity_label):
                """
                Sorts a list of model fields according to a defined order.


                :param list_unsorted: list
                    The unsorted list of fields.

                :param entity_label: str
                    The string representation of entity type, necessary to find the entity-specific ordering (if it is defined)


                :return: list
                    The sorted list if entity-specific ordering was defined, the same unordered list if not.
                """

                entity_settings = getattr(settings, "APIS_ENTITIES", None)

                if entity_settings is None:
                    return list_unsorted

                sort_preferences = entity_settings[entity_label].get("form_order", None)
                sort_preferences_used = []

                if sort_preferences is None:
                    return list_unsorted
                else:
                    # list of tuples to be sorted later
                    field_rank_pair_list = []
                    for field in list_unsorted:
                        if field in sort_preferences:
                            # if this succeeds, then the field has been given a priorites ordering above
                            ranking_by_index = sort_preferences.index(field)
                            sort_preferences_used.append(field)
                            field_rank_pair = (field, ranking_by_index)
                        else:
                            # if no ordering for the field was found, then give it 'Inf'
                            # so that it will be attached at the end.
                            field_rank_pair = (field, float("Inf"))
                        field_rank_pair_list.append(field_rank_pair)
                    # Make a check if all items of sort_preferences were used. If not, this indicates an out of sync setting
                    # if len(sort_preferences) > 0:
                    if len(sort_preferences_used) != len(sort_preferences):
                        differences = []
                        for p in sort_preferences_used:
                            if p not in sort_preferences:
                                differences.append(p)
                        for p in sort_preferences:
                            if p not in sort_preferences_used:
                                differences.append(p)

                        raise Exception(
                            "An item of the entity setting 'form_order' list was not used. \n"
                            "This propably indicates that the 'form_order' settings is out \n"
                            "of sync with the effective django models.\n"
                            f"The relevant entity is: {entity_label}\n"
                            f"And the differences between used list and settings list are: {differences}"
                        )
                    # sort the list according to the second element in each tuple
                    # and then take the first elements from it and return as list
                    return [
                        t[0] for t in sorted(field_rank_pair_list, key=lambda x: x[1])
                    ]

            # sort field list, iterate over it and append each element to the accordion group
            for f in sort_fields_list(fields_list_unsorted, entity):
                acc_grp1.append(f)

            self.helper.layout = Layout(Accordion(acc_grp1, acc_grp2))
            self.fields["status"].required = False
            self.fields["collection"].required = False
            self.fields["start_date_written"].required = False
            self.fields["end_date_written"].required = False

            instance = getattr(self, "instance", None)
            if instance != None:
                if instance.start_date_written:
                    self.fields[
                        "start_date_written"
                    ].help_text = DateParser.get_date_help_text_from_dates(
                        single_date=instance.start_date,
                        single_start_date=instance.start_start_date,
                        single_end_date=instance.start_end_date,
                        single_date_written=instance.start_date_written,
                    )
                else:
                    self.fields[
                        "start_date_written"
                    ].help_text = DateParser.get_date_help_text_default()

                if instance.end_date_written:
                    self.fields[
                        "end_date_written"
                    ].help_text = DateParser.get_date_help_text_from_dates(
                        single_date=instance.end_date,
                        single_start_date=instance.end_start_date,
                        single_end_date=instance.end_end_date,
                        single_date_written=instance.end_date_written,
                    )
                else:
                    self.fields[
                        "end_date_written"
                    ].help_text = DateParser.get_date_help_text_default()

        def save(self, *args, **kwargs):
            obj = super(GenericEntitiesForm, self).save(*args, **kwargs)
            if obj.collection.all().count() == 0:
                col_name = getattr(
                    settings, "APIS_DEFAULT_COLLECTION", "manually created entity"
                )
                col, created = Collection.objects.get_or_create(name=col_name)
                obj.collection.add(col)
            return obj

    return GenericEntitiesForm
