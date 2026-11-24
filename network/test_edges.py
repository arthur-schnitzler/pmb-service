from datetime import date
from unittest import mock

from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from apis_core.apis_entities.models import Person, Place
from apis_core.apis_relations.models import PersonPlace, PlacePlace
from apis_core.apis_vocabularies.models import PersonPlaceRelation, PlacePlaceRelation
from network.models import Edge


class EdgesCommandTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = Person.objects.create(name="Bahr", first_name="Hermann")
        cls.place = Place.objects.create(name="Linz", lat=48.3, lng=14.3)
        cls.other_place = Place.objects.create(name="Wien", lat=48.2, lng=16.3)
        cls.person_place_type = PersonPlaceRelation.objects.create(name="wohnt in")
        cls.place_place_type = PlacePlaceRelation.objects.create(name="nahe")
        cls.relations = [
            PersonPlace.objects.create(
                related_person=cls.person,
                related_place=cls.place,
                relation_type=cls.person_place_type,
                start_date_written="1900",
            )
            for _ in range(3)
        ]
        cls.place_relation = PlacePlace.objects.create(
            related_placea=cls.place,
            related_placeb=cls.other_place,
            relation_type=cls.place_place_type,
        )

    def run_edges(self):
        with (
            mock.patch(
                "network.management.commands.edges.AbstractRelation.get_all_relation_classes",
                return_value=[PersonPlace, PlacePlace],
            ),
            mock.patch("network.management.commands.edges.BATCH_SIZE", 2),
            mock.patch("network.management.commands.edges.write_report") as report,
        ):
            call_command("edges")
        report.assert_called_once()

    def test_rebuilds_in_bounded_batches_with_related_data(self):
        Edge.objects.create(
            edge_id=0,
            edge_kind="personplace",
            source_label="old",
            source_kind="person",
            source_id=1,
            edge_label="old",
            target_label="old",
            target_kind="place",
            target_id=2,
        )

        with CaptureQueriesContext(connection) as queries:
            self.run_edges()

        self.assertEqual(Edge.objects.count(), 4)
        edge = Edge.objects.get(edge_id=self.relations[0].pk, edge_kind="personplace")
        self.assertEqual(edge.source_label, "Bahr, Hermann")
        self.assertEqual(edge.source_id, self.person.pk)
        self.assertEqual(edge.source_kind, "person")
        self.assertEqual(edge.edge_label, "wohnt in")
        self.assertEqual(edge.target_label, "Linz")
        self.assertEqual(edge.target_id, self.place.pk)
        self.assertEqual(edge.target_kind, "place")
        self.assertEqual((edge.target_lat, edge.target_lng), (48.3, 14.3))
        self.assertIsNone(edge.source_lat)
        self.assertEqual(edge.start_date, date(1900, 1, 1))
        self.assertEqual(edge.end_date, self.relations[0].end_date)
        place_edge = Edge.objects.get(
            edge_id=self.place_relation.pk, edge_kind="placeplace"
        )
        self.assertEqual((place_edge.source_lat, place_edge.source_lng), (48.3, 14.3))
        self.assertEqual((place_edge.target_lat, place_edge.target_lng), (48.2, 16.3))
        self.assertCountEqual(
            Edge.objects.filter(edge_kind="personplace").values_list(
                "edge_id", flat=True
            ),
            [relation.pk for relation in self.relations],
        )
        selects = [
            query["sql"]
            for query in queries
            if query["sql"].lstrip().upper().startswith("SELECT")
        ]
        # One count and at most one query per page (including the final empty page).
        self.assertEqual(len(selects), 8)

    def test_failure_rolls_back_old_and_new_edges(self):
        old = Edge.objects.create(
            edge_id=0,
            edge_kind="personplace",
            source_label="old",
            source_kind="person",
            source_id=1,
            edge_label="old",
            target_label="old",
            target_kind="place",
            target_id=2,
        )
        bulk_create = Edge.objects.bulk_create
        calls = 0

        def fail_second_batch(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("insert failed")
            return bulk_create(*args, **kwargs)

        with (
            mock.patch(
                "network.management.commands.edges.AbstractRelation.get_all_relation_classes",
                return_value=[PersonPlace],
            ),
            mock.patch("network.management.commands.edges.BATCH_SIZE", 2),
            mock.patch.object(
                Edge.objects, "bulk_create", side_effect=fail_second_batch
            ),
            mock.patch("network.management.commands.edges.write_report") as report,
            self.assertRaisesRegex(RuntimeError, "insert failed"),
        ):
            call_command("edges")
        self.assertEqual(list(Edge.objects.values_list("pk", flat=True)), [old.pk])
        report.assert_not_called()
