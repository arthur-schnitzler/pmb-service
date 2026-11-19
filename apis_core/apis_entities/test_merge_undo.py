from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apis_core.apis_entities.models import Person, Place
from apis_core.apis_labels.models import Label
from apis_core.apis_metainfo.errors import MergeUndoError
from apis_core.apis_metainfo.models import (
    Collection,
    MergeLog,
    TempEntityClass,
    Uri,
)
from apis_core.apis_relations.models import PersonPerson, PersonPlace
from apis_core.apis_vocabularies.models import (
    PersonPersonRelation,
    PersonPlaceRelation,
    ProfessionType,
)

USER = {"username": "undouser", "password": "somepassword"}


class MergeUndoTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(**USER)
        self.client = Client()
        self.client.login(**USER)
        self.target = Person.objects.create(
            name="Bahr", first_name="Hermann", notes="target notes"
        )
        self.source = Person.objects.create(
            name="Bahr",
            first_name="Herrmann",
            notes="source notes",
            gender="male",
            start_date_written="1863",
            end_date_written="1934",
        )
        self.source_pk = self.source.pk
        self.other = Person.objects.create(name="Schnitzler", first_name="Arthur")
        self.place = Place.objects.create(name="Linz")
        pp_type = PersonPersonRelation.objects.create(name="kennt")
        pl_type = PersonPlaceRelation.objects.create(name="geboren in")
        self.rel_pp = PersonPerson.objects.create(
            related_persona=self.other,
            related_personb=self.source,
            relation_type=pp_type,
        )
        self.rel_self = PersonPerson.objects.create(
            related_persona=self.target,
            related_personb=self.source,
            relation_type=pp_type,
        )
        self.rel_target = PersonPerson.objects.create(
            related_persona=self.target,
            related_personb=self.other,
            relation_type=pp_type,
        )
        self.rel_pl = PersonPlace.objects.create(
            related_person=self.source, related_place=self.place, relation_type=pl_type
        )
        self.gnd = Uri.objects.create(
            uri="https://d-nb.info/gnd/118505955", domain="gnd", entity=self.source
        )
        self.label = Label.objects.create(label="H. Bahr", temp_entity=self.source)
        self.collection = Collection.objects.create(name="Bahr-Projekt")
        self.source.collection.add(self.collection)
        self.profession = ProfessionType.objects.create(name="Schriftsteller")
        self.source.profession.add(self.profession)
        self.pmb_uri = Uri.objects.get(entity=self.source, domain="pmb")

    def merge(self):
        self.target.merge_with(self.source_pk, user=self.user)
        self.target.refresh_from_db()
        return MergeLog.objects.get(source_pk=self.source_pk)

    def test_merge_creates_log(self):
        log = self.merge()
        self.assertFalse(Person.objects.filter(pk=self.source_pk).exists())
        self.assertEqual(log.target_pk, self.target.pk)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.source_model, "person")
        self.assertTrue(log.can_undo)
        # gender is inherited and persisted
        self.assertEqual(self.target.gender, "male")
        self.assertEqual(self.target.start_date_written, "1863")

    def test_undo_restores_entity(self):
        log = self.merge()
        warnings = log.undo(user=self.user)
        self.assertEqual(warnings, [])

        source = Person.objects.get(pk=self.source_pk)
        self.assertEqual(source.first_name, "Herrmann")
        self.assertEqual(source.notes, "source notes")
        self.assertEqual(source.start_date_written, "1863")
        self.assertEqual(list(source.collection.all()), [self.collection])
        self.assertEqual(list(source.profession.all()), [self.profession])

        # uris and labels are back, the legacy label is gone
        self.pmb_uri.refresh_from_db()
        self.gnd.refresh_from_db()
        self.assertEqual(self.pmb_uri.entity_id, self.source_pk)
        self.assertEqual(self.gnd.entity_id, self.source_pk)
        self.label.refresh_from_db()
        self.assertEqual(self.label.temp_entity_id, self.source_pk)
        self.assertFalse(
            Label.objects.filter(
                temp_entity=self.target, label_type__name="Legacy name (merge)"
            ).exists()
        )
        self.assertEqual(Uri.objects.filter(entity_id=self.source_pk).count(), 2)

        # relations are back
        for rel in [self.rel_pp, self.rel_self, self.rel_target, self.rel_pl]:
            rel.refresh_from_db()
        self.assertEqual(self.rel_pp.related_personb_id, self.source_pk)
        self.assertEqual(self.rel_self.related_persona_id, self.target.pk)
        self.assertEqual(self.rel_self.related_personb_id, self.source_pk)
        self.assertEqual(self.rel_target.related_persona_id, self.target.pk)
        self.assertEqual(self.rel_pl.related_person_id, self.source_pk)

        # target is reset
        target = Person.objects.get(pk=self.target.pk)
        self.assertEqual(target.notes, "target notes")
        self.assertEqual(target.gender, None)
        self.assertEqual(target.start_date_written, None)
        self.assertEqual(target.collection.count(), 0)
        self.assertEqual(target.profession.count(), 0)

        log.refresh_from_db()
        self.assertIsNotNone(log.undone_at)
        self.assertEqual(log.undone_by, self.user)
        with self.assertRaises(MergeUndoError):
            log.undo()

    def test_undo_keeps_later_changes(self):
        log = self.merge()
        self.target.notes = "edited after merge"
        self.target.save()
        self.rel_pl.delete()
        warnings = log.undo()
        self.assertEqual(len(warnings), 2)
        self.assertEqual(
            Person.objects.get(pk=self.target.pk).notes, "edited after merge"
        )
        self.assertTrue(Person.objects.filter(pk=self.source_pk).exists())

    def test_undo_deadline(self):
        log = self.merge()
        MergeLog.objects.filter(pk=log.pk).update(
            created=timezone.now() - timedelta(days=15)
        )
        log.refresh_from_db()
        self.assertFalse(log.can_undo)
        with self.assertRaises(MergeUndoError):
            log.undo()

    @override_settings(MERGE_UNDO_DAYS=30)
    def test_undo_deadline_setting(self):
        log = self.merge()
        MergeLog.objects.filter(pk=log.pk).update(
            created=timezone.now() - timedelta(days=15)
        )
        log.refresh_from_db()
        self.assertTrue(log.can_undo)

    def test_undo_view(self):
        log = self.merge()
        edit_url = reverse(
            "apis:apis_entities:generic_entities_edit_view",
            kwargs={"entity": "person", "pk": self.target.pk},
        )
        r = self.client.get(edit_url)
        self.assertContains(r, "bi-arrow-counterclockwise")
        self.assertContains(
            r, reverse("apis:apis_entities:undo_merge_view", kwargs={"pk": log.pk})
        )
        url = reverse("apis:apis_entities:undo_merge_view", kwargs={"pk": log.pk})
        self.assertEqual(self.client.get(url).status_code, 405)
        r = self.client.post(url, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "rückgängig gemacht")
        self.assertTrue(Person.objects.filter(pk=self.source_pk).exists())

    def test_undo_view_requires_login(self):
        log = self.merge()
        url = reverse("apis:apis_entities:undo_merge_view", kwargs={"pk": log.pk})
        r = Client().post(url)
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Person.objects.filter(pk=self.source_pk).exists())

    def test_merge_view_records_user(self):
        url = reverse(
            "apis:apis_entities:merge_view",
            kwargs={"entity": "person", "ent_merge_pk": self.source_pk},
        )
        self.client.post(url, {"entity": self.target.pk})
        log = MergeLog.objects.get(source_pk=self.source_pk)
        self.assertEqual(log.user, self.user)

    def test_str(self):
        log = self.merge()
        self.assertEqual(
            str(log), f"{log.source_name} ({self.source_pk}) -> {self.target.pk}"
        )

    def test_undo_restores_relation_with_source_on_side_a(self):
        rel = PersonPerson.objects.create(
            related_persona=self.source,
            related_personb=self.other,
            relation_type=self.rel_pp.relation_type,
        )
        log = self.merge()
        rel.refresh_from_db()
        self.assertEqual(rel.related_persona_id, self.target.pk)
        self.assertEqual(log.undo(), [])
        rel.refresh_from_db()
        self.assertEqual(rel.related_persona_id, self.source_pk)

    def test_undo_warns_about_uris_and_labels_moved_away(self):
        log = self.merge()
        self.gnd.entity = self.other
        self.gnd.save()
        self.label.temp_entity = self.other
        self.label.save()
        warnings = log.undo()
        self.assertEqual(len(warnings), 2)
        self.assertIn("URI", warnings[0])
        self.assertIn("Label", warnings[1])
        self.gnd.refresh_from_db()
        self.assertEqual(self.gnd.entity_id, self.other.pk)

    def test_undo_blocked_when_target_deleted(self):
        log = self.merge()
        self.target.delete()
        self.assertEqual(log.undo_blocker(), "Die Ziel-Entität existiert nicht mehr.")
        with self.assertRaises(MergeUndoError):
            log.undo()

    def test_undo_blocked_when_source_id_taken(self):
        log = self.merge()
        TempEntityClass.objects.create(pk=self.source_pk, name="Platzhalter")
        self.assertIn(str(self.source_pk), log.undo_blocker())
        self.assertFalse(log.can_undo)

    def test_undo_without_target_changes_keeps_later_edits(self):
        # a bare source changes none of the tracked target fields
        bare = Person.objects.create(name="Bahr", first_name="H.")
        bare_pk = bare.pk
        self.target.merge_with(bare_pk, user=self.user)
        log = MergeLog.objects.get(source_pk=bare_pk)
        self.target.refresh_from_db()
        self.target.references = "added after merge"
        self.target.save()
        self.assertEqual(log.undo(), [])
        self.assertTrue(Person.objects.filter(pk=bare_pk).exists())
        self.assertEqual(
            Person.objects.get(pk=self.target.pk).references, "added after merge"
        )

    def test_undo_view_shows_error(self):
        log = self.merge()
        log.undo()
        url = reverse("apis:apis_entities:undo_merge_view", kwargs={"pk": log.pk})
        r = self.client.post(url)
        self.assertRedirects(
            r,
            reverse(
                "apis:apis_entities:generic_entities_edit_view",
                kwargs={"entity": "person", "pk": self.target.pk},
            ),
            fetch_redirect_response=False,
        )
        r = self.client.get(r.url)
        self.assertContains(r, "bereits rückgängig gemacht")

    def test_undo_view_shows_warnings(self):
        log = self.merge()
        self.rel_pl.delete()
        url = reverse("apis:apis_entities:undo_merge_view", kwargs={"pk": log.pk})
        r = self.client.post(url, follow=True)
        self.assertContains(r, "nicht zurückverschoben")
