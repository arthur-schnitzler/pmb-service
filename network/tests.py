from datetime import date
from unittest.mock import patch

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse

from apis_core.apis_entities.models import Person, Place
from apis_core.apis_relations.models import PersonPerson, PersonPlace, PlacePlace
from apis_core.apis_vocabularies.models import (
    PersonPersonRelation,
    PersonPlaceRelation,
    PlacePlaceRelation,
)
from network.models import Edge

client = Client()
USER = {"username": "testuser", "password": "password", "is_active": True}
BAHR = {"name": "Schnitzler", "first_name": "Hermann", "start_date_written": "1900"}

ENTITY_TYPES = ["person", "place", "event", "work", "institution"]

MODELS = list(apps.all_models["apis_entities"].values())
MEDIA_ROOT = settings.MEDIA_ROOT


class RelationEdgeSyncTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = Person.objects.create(name="Bahr", first_name="Hermann")
        cls.place = Place.objects.create(name="Linz", lat=48.3, lng=14.3)
        cls.rel_type = PersonPlaceRelation.objects.create(name="wohnt in")

    def create_relation(self):
        return PersonPlace.objects.create(
            related_person=self.person,
            related_place=self.place,
            relation_type=self.rel_type,
            start_date_written="1900",
        )

    def test_create_and_update_edge(self):
        relation = self.create_relation()
        edge = Edge.objects.get(edge_id=relation.pk, edge_kind="personplace")
        self.assertEqual(edge.source_label, str(self.person)[:249])
        self.assertEqual(edge.target_label, str(self.place)[:249])
        self.assertEqual((edge.source_kind, edge.target_kind), ("person", "place"))
        self.assertEqual((edge.source_id, edge.target_id), (self.person.pk, self.place.pk))
        self.assertEqual((edge.target_lat, edge.target_lng), (48.3, 14.3))
        self.assertEqual(edge.edge_label, str(self.rel_type))
        self.assertEqual(edge.start_date, date(1900, 1, 1))

        other = Place.objects.create(name="Wien", lat=48.2, lng=16.3)
        relation.related_place = other
        relation.start_date_written = "1910"
        relation.save()
        edge.refresh_from_db()
        self.assertEqual(edge.target_id, other.pk)
        self.assertEqual(edge.target_label, str(other)[:249])
        self.assertEqual((edge.target_lat, edge.target_lng), (48.2, 16.3))
        self.assertEqual(edge.start_date, date(1910, 1, 1))
        self.assertEqual(Edge.objects.filter(edge_id=relation.pk, edge_kind="personplace").count(), 1)

    def test_partial_save_uses_persisted_values(self):
        relation = self.create_relation()
        relation.related_place = Place.objects.create(name="Wien")
        relation.notes = "Changed"
        relation.save(update_fields=["notes"])
        edge = Edge.objects.get(edge_id=relation.pk, edge_kind="personplace")
        self.assertEqual(edge.target_id, self.place.pk)
        self.assertEqual(edge.start_date, date(1900, 1, 1))

    def test_saving_relation_recreates_missing_edge(self):
        relation = self.create_relation()
        Edge.objects.filter(edge_id=relation.pk, edge_kind="personplace").delete()
        relation.save()
        self.assertTrue(
            Edge.objects.filter(edge_id=relation.pk, edge_kind="personplace").exists()
        )

    def test_empty_update_fields_does_not_create_edge_for_unsaved_relation(self):
        relation = PersonPlace(
            related_person=self.person,
            related_place=self.place,
            relation_type=self.rel_type,
        )
        relation.save(update_fields=[])
        self.assertIsNone(relation.pk)
        self.assertFalse(Edge.objects.exists())

    def test_place_on_both_sides(self):
        other = Place.objects.create(name="Wien", lat=48.2, lng=16.3)
        rel_type = PlacePlaceRelation.objects.create(name="nahe")
        relation = PlacePlace.objects.create(
            related_placea=self.place, related_placeb=other, relation_type=rel_type
        )
        edge = Edge.objects.get(edge_id=relation.pk, edge_kind="placeplace")
        self.assertEqual((edge.source_lat, edge.source_lng), (48.3, 14.3))
        self.assertEqual((edge.target_lat, edge.target_lng), (48.2, 16.3))

    def test_delete_instance_queryset_and_cascade(self):
        for deletion in ("instance", "queryset", "cascade"):
            with self.subTest(deletion=deletion):
                relation = self.create_relation()
                relation_id = relation.pk
                self.assertTrue(Edge.objects.filter(edge_id=relation_id, edge_kind="personplace").exists())
                if deletion == "instance":
                    relation.delete()
                elif deletion == "queryset":
                    PersonPlace.objects.filter(pk=relation_id).delete()
                else:
                    self.place.delete()
                self.assertFalse(Edge.objects.filter(edge_id=relation_id, edge_kind="personplace").exists())

    def test_deletion_does_not_remove_other_edge_kind(self):
        relation = self.create_relation()
        other_type = PersonPersonRelation.objects.create(name="kennt")
        other = PersonPerson.objects.create(
            related_persona=self.person, related_personb=self.person, relation_type=other_type
        )
        Edge.objects.filter(edge_id=other.pk, edge_kind="personperson").update(edge_id=relation.pk)
        relation_id = relation.pk
        relation.delete()
        self.assertTrue(Edge.objects.filter(edge_id=relation_id, edge_kind="personperson").exists())

    def test_edge_failure_rolls_back_relation(self):
        with (
            self.assertRaises(IntegrityError),
            transaction.atomic(),
            patch.object(Edge, "sync_from_relation", side_effect=IntegrityError),
        ):
            self.create_relation()
        self.assertFalse(PersonPlace.objects.exists())


class DumperTestCase(TestCase):
    fixtures = [
        "network.json",
    ]

    def test_01_network(self):
        url = reverse("network:network")
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_01a_network_data(self):
        url = reverse("network:data")
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_01b_network_data(self):
        url = f"{reverse('network:data')}?format=hansi"
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_01c_network_data(self):
        url = f"{reverse('network:data')}?format=json"
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_01d_network_data(self):
        url = f"{reverse('network:data')}?format=cosmograph"
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_02_edge_list_view(self):
        url = reverse("network:edges_browse")
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_03_map_view(self):
        url = reverse("network:map")
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_04_geojson_view(self):
        url = reverse("network:geojson")
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_05_calendar_data(self):
        url = reverse("network:calender_data")
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_06_tei_relation(self):
        url = reverse("network:tei")
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_07_tei_relations_command(self):
        call_command("tei_relations")
