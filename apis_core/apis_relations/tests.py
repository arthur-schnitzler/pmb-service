from django.core.exceptions import ValidationError
from django.test import TestCase

from apis_core.apis_relations.forms2 import (
    GenericRelationForm,
    normalize_target_autocomplete_value,
)


class GenericRelationFormTestCase(TestCase):
    # fixtures = [
    #     "db.json",
    # ]

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


class InverseRelationTypeTestCase(TestCase):
    """Relation types replaced by their canonical inverse (see #553)."""

    def setUp(self):
        from apis_core.apis_entities.models import Person
        from apis_core.apis_vocabularies.models import PersonPersonRelation

        self.parent_type = PersonPersonRelation.objects.create(
            name="ist Elternteil von", name_reverse="ist Kind von"
        )
        self.child_type = PersonPersonRelation.objects.create(
            name="ist Kind von", name_reverse="ist Elternteil von"
        )
        self.sibling_type = PersonPersonRelation.objects.create(
            name="ist Geschwister von", name_reverse="ist Geschwister von"
        )
        self.parent = Person.objects.create(name="Schnitzler", first_name="Johann")
        self.child = Person.objects.create(name="Schnitzler", first_name="Arthur")

    def deprecate_child_type(self):
        self.child_type.canonical_inverse = self.parent_type
        self.child_type.save()

    def test_save_swaps_deprecated_type(self):
        from apis_core.apis_relations.models import PersonPerson

        self.deprecate_child_type()
        rel = PersonPerson.objects.create(
            related_persona=self.child,
            related_personb=self.parent,
            relation_type=self.child_type,
        )
        rel.refresh_from_db()
        self.assertEqual(rel.related_persona, self.parent)
        self.assertEqual(rel.related_personb, self.child)
        self.assertEqual(rel.relation_type_id, self.parent_type.pk)

    def test_save_keeps_canonical_type(self):
        from apis_core.apis_relations.models import PersonPerson

        rel = PersonPerson.objects.create(
            related_persona=self.child,
            related_personb=self.parent,
            relation_type=self.child_type,
        )
        rel.refresh_from_db()
        self.assertEqual(rel.related_persona, self.child)
        self.assertEqual(rel.relation_type_id, self.child_type.pk)

    def test_clean_rejects_self_and_chains(self):
        self.child_type.canonical_inverse = self.child_type
        with self.assertRaises(ValidationError):
            self.child_type.clean()
        self.deprecate_child_type()
        self.sibling_type.canonical_inverse = self.child_type
        with self.assertRaises(ValidationError):
            self.sibling_type.clean()
        self.parent_type.canonical_inverse = self.sibling_type
        with self.assertRaises(ValidationError):
            self.parent_type.clean()

    def test_clean_rejects_relations_between_different_classes(self):
        from apis_core.apis_vocabularies.models import PersonPlaceRelation

        lives = PersonPlaceRelation.objects.create(name="wohnt in", name_reverse="Wohnort von")
        other = PersonPlaceRelation.objects.create(name="Wohnort von", name_reverse="wohnt in")
        other.canonical_inverse = lives
        with self.assertRaises(ValidationError):
            other.clean()

    def test_autocomplete_offers_both_readings_without_deprecated_types(self):
        from django.urls import reverse

        self.deprecate_child_type()
        url = reverse(
            "apis:apis_vocabularies:generic_vocabularies_autocomplete",
            args=["personpersonrelation", "both"],
        )
        results = self.client.get(url).json()["results"]
        self.assertIn(
            {"id": f"{self.parent_type.pk}", "text": "ist Elternteil von"}, results
        )
        self.assertIn({"id": f"{self.parent_type.pk}:r", "text": "ist Kind von"}, results)
        # symmetric types only once, deprecated types not at all
        self.assertEqual(
            [r["id"] for r in results if r["text"] == "ist Geschwister von"],
            [f"{self.sibling_type.pk}"],
        )
        self.assertNotIn(f"{self.child_type.pk}", [r["id"] for r in results])
        filtered = self.client.get(url, {"q": "Kind"}).json()["results"]
        self.assertEqual(
            filtered, [{"id": f"{self.parent_type.pk}:r", "text": "ist Kind von"}]
        )

    def relation_form_data(self, relation_type, target):
        return {
            "relation_type": relation_type,
            "target": f"{target.pk}",
            "start_date_written": "",
            "end_date_written": "",
            "references": "",
            "notes": "",
        }

    def test_form_reverse_reading_stores_current_person_as_target(self):
        form = GenericRelationForm(
            entity_type="person",
            relation_form="PersonPerson",
            data=self.relation_form_data(f"{self.parent_type.pk}:r", self.parent),
        )
        self.assertTrue(form.is_valid(), msg=form.errors.as_json())
        rel = form.save(site_instance=self.child)
        rel.refresh_from_db()
        self.assertEqual(rel.related_persona, self.parent)
        self.assertEqual(rel.related_personb, self.child)
        self.assertEqual(rel.relation_type_id, self.parent_type.pk)

    def test_form_normal_reading_stores_current_person_as_source(self):
        form = GenericRelationForm(
            entity_type="person",
            relation_form="PersonPerson",
            data=self.relation_form_data(f"{self.parent_type.pk}", self.child),
        )
        self.assertTrue(form.is_valid(), msg=form.errors.as_json())
        rel = form.save(site_instance=self.parent)
        rel.refresh_from_db()
        self.assertEqual(rel.related_persona, self.parent)
        self.assertEqual(rel.related_personb, self.child)

    def test_form_edit_from_target_side_keeps_direction(self):
        from apis_core.apis_relations.models import PersonPerson

        rel = PersonPerson.objects.create(
            related_persona=self.parent,
            related_personb=self.child,
            relation_type=self.parent_type,
        )
        form = GenericRelationForm(
            entity_type="person",
            relation_form="PersonPerson",
            instance=rel,
            siteID=self.child.pk,
        )
        self.assertEqual(
            form.fields["relation_type"].initial,
            (f"{self.parent_type.pk}:r", "ist Kind von"),
        )
        data = self.relation_form_data(f"{self.parent_type.pk}:r", self.parent)
        data["start_date_written"] = "1862"
        form = GenericRelationForm(
            entity_type="person", relation_form="PersonPerson", data=data
        )
        self.assertTrue(form.is_valid(), msg=form.errors.as_json())
        form.save(site_instance=self.child, instance=rel.pk)
        rel.refresh_from_db()
        self.assertEqual(rel.related_persona, self.parent)
        self.assertEqual(rel.related_personb, self.child)
        self.assertEqual(rel.start_date_written, "1862")

    def test_form_rejects_reverse_reading_for_different_classes(self):
        from apis_core.apis_entities.models import Place

        place = Place.objects.create(name="Wien")
        form = GenericRelationForm(
            entity_type="person",
            relation_form="PersonPlace",
            data=self.relation_form_data("1:r", place),
        )
        self.assertFalse(form.is_valid())
        self.assertIn("relation_type", form.errors)


class NormalizeInverseRelationsCommandTestCase(TestCase):
    def setUp(self):
        from apis_core.apis_entities.models import Person
        from apis_core.apis_vocabularies.models import PersonPersonRelation

        self.parent_type = PersonPersonRelation.objects.create(
            name="ist Elternteil von", name_reverse="ist Kind von"
        )
        self.child_type = PersonPersonRelation.objects.create(
            name="ist Kind von", name_reverse="ist Elternteil von"
        )
        self.persons = [
            Person.objects.create(name=f"Person {i}") for i in range(6)
        ]

    def create(self, a, b, relation_type, **kwargs):
        from apis_core.apis_relations.models import PersonPerson

        return PersonPerson.objects.create(
            related_persona=self.persons[a],
            related_personb=self.persons[b],
            relation_type=relation_type,
            **kwargs,
        )

    def run_command(self, *args):
        from io import StringIO

        from django.core.management import call_command

        out = StringIO()
        call_command("normalize_inverse_relations", *args, stdout=out, stderr=StringIO())
        return out.getvalue()

    def test_dry_run_changes_nothing(self):
        rel = self.create(1, 0, self.child_type)
        out = self.run_command("--mark", f"{self.child_type.pk}:{self.parent_type.pk}")
        self.assertIn("dry run", out)
        self.assertIn("'flip': 1", out)
        rel.refresh_from_db()
        self.child_type.refresh_from_db()
        self.assertEqual(rel.relation_type_id, self.child_type.pk)
        self.assertIsNone(self.child_type.canonical_inverse_id)

    def test_apply_flips_merges_and_skips_conflicts(self):
        from apis_core.apis_relations.models import PersonPerson

        flip = self.create(1, 0, self.child_type)
        # mirrored duplicate without contradicting data -> merged
        kept = self.create(2, 3, self.parent_type, start_date_written="1862")
        merged = self.create(3, 2, self.child_type, notes="aus Taufbuch")
        # same period, but contradicting notes -> left alone
        self.create(4, 5, self.parent_type, notes="laut Meldezettel")
        conflict = self.create(5, 4, self.child_type, notes="laut Tagebuch")
        # mirrored relation with a different period is a distinct relation -> flipped
        self.create(0, 2, self.parent_type, start_date_written="1870", end_date_written="1875")
        other_period = self.create(
            2, 0, self.child_type, start_date_written="1880", end_date_written="1885"
        )

        out = self.run_command(
            "--mark", f"{self.child_type.pk}:{self.parent_type.pk}", "--apply"
        )
        self.assertIn("'flip': 2", out)
        self.assertIn("'merge': 1", out)
        self.assertIn("'conflict': 1", out)
        other_period.refresh_from_db()
        self.assertEqual(
            (other_period.related_persona, other_period.relation_type_id),
            (self.persons[0], self.parent_type.pk),
        )

        flip.refresh_from_db()
        self.assertEqual(
            (flip.related_persona, flip.related_personb, flip.relation_type_id),
            (self.persons[0], self.persons[1], self.parent_type.pk),
        )
        self.assertFalse(PersonPerson.objects.filter(pk=merged.pk).exists())
        kept.refresh_from_db()
        self.assertEqual(kept.start_date_written, "1862")
        self.assertEqual(kept.notes, "aus Taufbuch")
        conflict.refresh_from_db()
        self.assertEqual(conflict.relation_type_id, self.child_type.pk)
        self.child_type.refresh_from_db()
        self.assertEqual(self.child_type.canonical_inverse_id, self.parent_type.pk)

    def test_report_lists_inverse_pairs(self):
        self.create(1, 0, self.child_type)
        out = self.run_command("--report")
        self.assertIn("'ist Elternteil von' (0)", out)
        self.assertIn("'ist Kind von' (1)", out)
