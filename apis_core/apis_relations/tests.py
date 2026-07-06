from django.core.exceptions import ValidationError
from django.test import TestCase

from apis_core.apis_relations.forms2 import (
    GenericRelationForm,
    normalize_target_autocomplete_value,
)


class GenericRelationFormTestCase(TestCase):
    fixtures = [
        "db.json",
    ]

    def test_autocomplete_off_on_all_fields(self):
        """All form fields disable browser autofill (see #451)."""
        form = GenericRelationForm(
            entity_type="person",
            relation_form="PersonPlace",
        )
        self.assertTrue(form.fields)
        for name, field in form.fields.items():
            self.assertEqual(
                field.widget.attrs.get("autocomplete"),
                "off",
                msg=f"field '{name}' is missing autocomplete='off'",
            )

    def test_normalize_target_autocomplete_value_accepts_numeric_id(self):
        self.assertEqual(normalize_target_autocomplete_value("44909"), "44909")

    def test_normalize_target_autocomplete_value_extracts_db_id_from_html_label(self):
        value = (
            "<span ><small>db</small> <b>Altaussee 43</b> "
            "<small>db-ID: 44909</small> </span>"
        )
        self.assertEqual(normalize_target_autocomplete_value(value), "44909")

    def test_normalize_target_autocomplete_value_accepts_urls(self):
        value = "https://example.org/entity/123"
        self.assertEqual(normalize_target_autocomplete_value(value), value)

    def test_normalize_target_autocomplete_value_rejects_plain_text(self):
        with self.assertRaises(ValidationError) as exc_info:
            normalize_target_autocomplete_value("Altaussee 43")

        self.assertEqual(exc_info.exception.code, "invalid")

    def test_form_is_valid_and_normalizes_html_target_value(self):
        form_combinations = [
            ("person", "PersonPlace"),
            ("person", "PersonPerson"),
            ("person", "PersonInstitution"),
            ("institution", "PersonInstitution"),
            ("person", "PersonEvent"),
            ("person", "PersonWork"),
            ("institution", "InstitutionPlace"),
            ("institution", "InstitutionInstitution"),
            ("institution", "InstitutionEvent"),
            ("institution", "InstitutionWork"),
            ("place", "PlaceEvent"),
            ("place", "PlaceWork"),
            ("place", "PlacePlace"),
            ("event", "EventWork"),
            ("event", "EventEvent"),
            ("work", "WorkWork"),
        ]

        for entity_type, relation_form in form_combinations:
            with self.subTest(entity_type=entity_type, relation_form=relation_form):
                form = GenericRelationForm(
                    entity_type=entity_type,
                    relation_form=relation_form,
                    data={
                        "relation_type": "1",
                        "target": (
                            "<span ><small>db</small> <b>Altaussee 43</b> "
                            "<small>db-ID: 44909</small> </span>"
                        ),
                        "start_date_written": "",
                        "end_date_written": "",
                        "references": "",
                        "notes": "",
                    },
                )

                self.assertTrue(form.is_valid(), msg=form.errors.as_json())
                self.assertEqual(form.cleaned_data["target"], "44909")
