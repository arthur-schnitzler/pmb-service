from django.test import TestCase

from apis_core.apis_relations.forms2 import GenericRelationForm


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
