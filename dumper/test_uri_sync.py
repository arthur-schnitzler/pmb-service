from io import StringIO
from unittest import mock

import requests
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from apis_core.apis_entities.models import Event, Institution, Person, Place, Work
from apis_core.apis_metainfo.models import Uri
from dumper.uri_sync import UriSyncError, load_csv

DOMAIN = "mein-projekt"
URL = "https://mein-projekt.example/pmb_uris-in-use.csv"
HEADER = "pmb_id,entity_type,uri,domain"


def project_uri(pmb_id):
    return f"https://mein-projekt.example/pmb{pmb_id}.html"


def csv_text(rows, header=HEADER):
    lines = [header] + [",".join(str(x) for x in row) for row in rows]
    return "\n".join(lines) + "\n"


def csv_rows(entities, domain=DOMAIN):
    return [
        (e.pk, entity_type, project_uri(e.pk), domain) for entity_type, e in entities
    ]


def fake_get(text):
    response = mock.Mock(content=text.encode("utf-8"))
    response.raise_for_status.return_value = None
    return mock.Mock(return_value=response)


@override_settings(PMB_URI_SOURCES={DOMAIN: URL})
class SyncUrisInUseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.persons = [Person.objects.create(name=f"person {i}") for i in range(40)]
        cls.place = Place.objects.create(name="place")
        cls.org = Institution.objects.create(name="org")
        cls.bibl = Work.objects.create(name="bibl")
        cls.event = Event.objects.create(name="event")

    def entities(self):
        return (
            [("person", p) for p in self.persons]
            + [("place", self.place), ("org", self.org)]
            + [("bibl", self.bibl), ("event", self.event)]
        )

    def sync(self, text, *args, **kwargs):
        out, err = StringIO(), StringIO()
        with mock.patch("dumper.uri_sync.requests.get", fake_get(text)):
            try:
                call_command(
                    "sync_uris_in_use", *args, stdout=out, stderr=err, **kwargs
                )
            except CommandError as e:
                raise CommandError(f"{e}\n{out.getvalue()}{err.getvalue()}") from e
        return out.getvalue()

    def project_uris(self):
        return Uri.objects.filter(domain=DOMAIN)

    def sync_all(self):
        return self.sync(csv_text(csv_rows(self.entities())))

    def test_01_first_run_adds_all_types(self):
        self.sync_all()
        self.assertEqual(self.project_uris().count(), len(self.entities()))
        uri = self.project_uris().get(entity_id=self.bibl.pk)
        self.assertEqual(uri.uri, project_uri(self.bibl.pk))

    def test_02_second_run_changes_nothing(self):
        self.sync_all()
        before = sorted(self.project_uris().values_list("pk", "uri", "entity_id"))
        out = self.sync_all()
        self.assertEqual(
            before, sorted(self.project_uris().values_list("pk", "uri", "entity_id"))
        )
        self.assertIn("0 added, 0 changed, 0 deleted", out)

    def test_03_changed_uri_is_updated_in_place(self):
        self.sync_all()
        old = self.project_uris().get(entity_id=self.place.pk)
        rows = csv_rows(self.entities())
        rows[40] = (
            self.place.pk,
            "place",
            "https://mein-projekt.example/neu.html",
            DOMAIN,
        )
        out = self.sync(csv_text(rows))
        self.assertIn("1 changed", out)
        old.refresh_from_db()
        self.assertEqual(old.uri, "https://mein-projekt.example/neu.html")
        self.assertEqual(self.project_uris().count(), len(self.entities()))

    def test_04_removed_row_deletes_exactly_one_uri(self):
        self.sync_all()
        rows = csv_rows(self.entities())
        gone = rows.pop(0)
        out = self.sync(csv_text(rows))
        self.assertIn("1 deleted", out)
        self.assertFalse(self.project_uris().filter(entity_id=gone[0]).exists())
        self.assertEqual(self.project_uris().count(), len(self.entities()) - 1)

    def test_05_other_domains_are_never_touched(self):
        other = Uri.objects.create(
            uri="https://anders.example/1", domain="anders", entity=self.place
        )
        gnd = Uri.objects.create(
            uri="https://d-nb.info/gnd/1", domain="gnd", entity=self.place
        )
        self.sync_all()
        rows = csv_rows(self.entities())[:35]
        self.sync(csv_text(rows), max_delete_ratio=1)
        self.assertEqual(Uri.objects.filter(pk__in=[other.pk, gnd.pk]).count(), 2)
        self.assertEqual(self.project_uris().count(), 35)

    def test_06_empty_csv_aborts_and_keeps_everything(self):
        self.sync_all()
        for text in ["", csv_text([])]:
            with self.assertRaises(CommandError):
                self.sync(text)
        self.assertEqual(self.project_uris().count(), len(self.entities()))

    def test_07_emergency_brake(self):
        self.sync_all()
        rows = csv_rows(self.entities())[:20]
        with self.assertRaises(CommandError):
            self.sync(csv_text(rows))
        self.assertEqual(self.project_uris().count(), len(self.entities()))
        self.sync(csv_text(rows), max_delete_ratio=1)
        self.assertEqual(self.project_uris().count(), 20)

    def test_08_dry_run_writes_nothing(self):
        out = self.sync_all_dry()
        self.assertIn(f"{len(self.entities())} added", out)
        self.assertEqual(self.project_uris().count(), 0)

    def sync_all_dry(self):
        return self.sync(csv_text(csv_rows(self.entities())), dry_run=True)

    def test_09_dry_run_reports_emergency_brake(self):
        self.sync_all()
        with self.assertRaises(CommandError):
            self.sync(csv_text(csv_rows(self.entities())[:20]), dry_run=True)

    def test_10_missing_entity_is_skipped_not_fatal(self):
        rows = csv_rows(self.entities()) + [
            (999999999, "person", project_uri(999999999), DOMAIN)
        ]
        out = self.sync(csv_text(rows))
        self.assertIn("1 skipped", out)
        self.assertIn("entity doesn't exist", out)
        self.assertEqual(self.project_uris().count(), len(self.entities()))

    def test_11_wrong_entity_type_is_skipped(self):
        rows = csv_rows(self.entities())
        rows[40] = (self.place.pk, "person", project_uri(self.place.pk), DOMAIN)
        out = self.sync(csv_text(rows))
        self.assertIn("entity has another type", out)
        self.assertFalse(self.project_uris().filter(entity_id=self.place.pk).exists())

    def test_12_merged_entity_keeps_its_uri_on_the_target(self):
        target = Person.objects.create(name="target")
        source = Person.objects.create(name="source")
        source_pk = source.pk
        rows = csv_rows(self.entities() + [("person", target), ("person", source)])
        self.sync(csv_text(rows))
        target.merge_with(source)
        self.assertFalse(Person.objects.filter(pk=source_pk).exists())

        # csv still lists the merged id and its page
        out = self.sync(csv_text(rows))
        self.assertIn("1 already merged", out)
        self.assertIn("0 added, 0 changed, 0 deleted", out)
        self.assertEqual(
            sorted(
                self.project_uris().filter(entity=target).values_list("uri", flat=True)
            ),
            sorted([project_uri(target.pk), project_uri(source_pk)]),
        )

        # once the project drops the merged page, only that uri goes away
        self.sync(csv_text(rows[:-1]))
        self.assertEqual(
            list(
                self.project_uris().filter(entity=target).values_list("uri", flat=True)
            ),
            [project_uri(target.pk)],
        )

    def test_13_uri_held_by_another_domain_is_a_conflict(self):
        Uri.objects.create(
            uri=project_uri(self.place.pk), domain="anders", entity=self.org
        )
        out = self.sync_all()
        self.assertIn("1 conflicts", out)
        self.assertFalse(self.project_uris().filter(entity_id=self.place.pk).exists())
        self.assertEqual(self.project_uris().count(), len(self.entities()) - 1)

    def test_14_unknown_domain_option(self):
        with self.assertRaises(CommandError):
            self.sync(csv_text([]), domain="gibt-es-nicht")

    def test_15_failing_project_does_not_stop_the_others(self):
        sources = {"kaputt": "https://kaputt.example/x.csv", DOMAIN: URL}
        text = csv_text(csv_rows(self.entities()))

        def get(url, **kwargs):
            if "kaputt" in url:
                raise requests.ConnectionError("down")
            return fake_get(text)(url, **kwargs)

        with (
            override_settings(PMB_URI_SOURCES=sources),
            mock.patch("dumper.uri_sync.requests.get", get),
            self.assertRaises(CommandError),
        ):
            call_command("sync_uris_in_use", stdout=StringIO(), stderr=StringIO())
        self.assertEqual(self.project_uris().count(), len(self.entities()))


class LoadCsvTestCase(TestCase):
    def load(self, text):
        with mock.patch("dumper.uri_sync.requests.get", fake_get(text)):
            return load_csv(URL, DOMAIN)

    def test_01_valid(self):
        rows = self.load(csv_text([(1, "person", project_uri(1), DOMAIN)]))
        self.assertEqual(rows, [("person", 1, project_uri(1))])

    def test_02_invalid(self):
        valid = (1, "person", project_uri(1), DOMAIN)
        cases = {
            "empty": "",
            "no header": csv_text([valid], header="a,b,c,d"),
            "no rows": csv_text([]),
            "foreign domain": csv_text([valid, (2, "person", project_uri(2), "x")]),
            "entity_type": csv_text([valid, (2, "work", project_uri(2), DOMAIN)]),
            "pmb_id": csv_text([valid, ("abc", "person", project_uri(2), DOMAIN)]),
            "empty uri": csv_text([valid, (2, "person", "", DOMAIN)]),
            "duplicate key": csv_text([valid, (1, "person", project_uri(2), DOMAIN)]),
            "duplicate uri": csv_text([valid, (2, "person", project_uri(1), DOMAIN)]),
        }
        for name, text in cases.items():
            with self.subTest(name), self.assertRaises(UriSyncError):
                self.load(text)

    def test_03_http_error(self):
        response = mock.Mock()
        response.raise_for_status.side_effect = requests.HTTPError("404")
        with (
            mock.patch(
                "dumper.uri_sync.requests.get", mock.Mock(return_value=response)
            ),
            self.assertRaises(UriSyncError),
        ):
            load_csv(URL, DOMAIN)

    def test_04_invalid_utf8(self):
        response = mock.Mock(content=b"\xff\xfe\x00")
        response.raise_for_status.return_value = None
        with (
            mock.patch(
                "dumper.uri_sync.requests.get", mock.Mock(return_value=response)
            ),
            self.assertRaises(UriSyncError),
        ):
            load_csv(URL, DOMAIN)
