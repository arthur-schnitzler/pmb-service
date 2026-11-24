# Create your tests here.

from unittest import mock

import requests
from django.apps import apps
from django.contrib.auth.models import User
from django.db import connection
from django.test import Client, SimpleTestCase, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apis_core.apis_entities.list_view_uris import UriTable
from apis_core.apis_entities.models import Event, Institution, Person, Place, Work
from apis_core.apis_metainfo.models import (
    Collection,
    TempEntityClass,
    Uri,
    fetch_image,
    normalize_wikimedia_img_url,
    pick_wikidata_image_name,
)

client = Client()
USER = {"username": "testuser", "password": "somepassword"}
BAHR = {"name": "Bahr", "first_name": "Hermann", "start_date_written": "1900"}
DUMMY_OBJECT = {"name": "test", "start_date_written": "1900"}

ENTITY_TYPES = ["person", "place", "event", "work", "institution"]

MODELS = list(apps.all_models["apis_entities"].values())

RELATION_MODELS = list(apps.all_models["apis_relations"].values())
DOMAIN = "hansi4ever"


class EntitiesTestCase(TestCase):
    def setUp(self):
        User.objects.create_user(**USER)

    def test_001_collection_domain_entities(self):
        ronja = Person.objects.create(name="Ronja")
        hanna = Person.objects.create(name="Hanna")
        Uri.objects.create(uri="https://foo/bar/roo/1", domain=DOMAIN, entity=ronja)
        Uri.objects.create(uri="https://foo/bar/roo/2", domain=DOMAIN, entity=ronja)
        col = Collection.objects.create(name="foo", related_domain=[DOMAIN])
        new_col = Collection.objects.create(
            name="foobar", related_domain=[DOMAIN, "karl"]
        )
        Uri.objects.create(uri="https://foo/bar/roo/3", domain="karl", entity=hanna)
        rel_ents = col.get_related_entities_count()
        print(f"#########################{rel_ents}")
        self.assertEqual(rel_ents, 1)
        rel_uris = col.get_related_uris().count()
        self.assertEqual(rel_uris, 2)

        rel_ents = new_col.get_related_entities_count()
        self.assertEqual(rel_ents, 2)
        print(f"#########################{rel_ents}")
        rel_uris = new_col.get_related_uris().count()
        self.assertEqual(rel_uris, 3)

    def test_002_quotes_in_name_are_converted(self):
        cases = {
            'Der "Reigen"': "Der »Reigen«",
            "Der “Reigen”": "Der »Reigen«",
            "Der „Reigen“": "Der »Reigen«",
            'Ein "A" und "B"': "Ein »A« und »B«",
            'Unbalanced "quote': 'Unbalanced "quote',
            "Der »Reigen«": "Der »Reigen«",
            "Dreher's Welt": "Dreher’s Welt",
            "Dreher's": "Dreher’s",
            "Dreher 'Welt'": "Dreher 'Welt'",
        }
        for raw, expected in cases.items():
            work = Work.objects.create(name=raw)
            work.refresh_from_db()
            self.assertEqual(work.name, expected)


class WikimediaImgUrlTestCase(TestCase):
    base = "https://upload.wikimedia.org/wikipedia/commons"

    def test_original_becomes_thumb(self):
        url = f"{self.base}/d/da/Otto_Brahm.jpg?utm_source=commons.wikimedia.org&utm_campaign=index&utm_content=original"
        self.assertEqual(
            normalize_wikimedia_img_url(url),
            f"{self.base}/thumb/d/da/Otto_Brahm.jpg/250px-Otto_Brahm.jpg",
        )

    def test_thumb_stays(self):
        url = (
            f"{self.base}/thumb/4/40/Hermann_Bahr_1891.jpg/250px-Hermann_Bahr_1891.jpg"
        )
        self.assertEqual(normalize_wikimedia_img_url(url), url)

    def test_svg_gets_png_suffix(self):
        self.assertEqual(
            normalize_wikimedia_img_url(f"{self.base}/a/ab/Wappen.svg"),
            f"{self.base}/thumb/a/ab/Wappen.svg/250px-Wappen.svg.png",
        )

    def test_special_filepath_gets_width(self):
        url = "https://commons.wikimedia.org/wiki/Special:FilePath/Mathilde%20Sussin%20%28Isabella%29%20by%20Becker%20%26%20Maass.jpg"
        self.assertEqual(normalize_wikimedia_img_url(url), f"{url}?width=250")
        self.assertEqual(
            normalize_wikimedia_img_url(f"{url}?width=250"), f"{url}?width=250"
        )

    def test_other_urls_untouched(self):
        url = "https://example.com/bild.jpg?x=1"
        self.assertEqual(normalize_wikimedia_img_url(url), url)
        self.assertIsNone(normalize_wikimedia_img_url(None))

    def test_wikimedia_url_without_thumb_support(self):
        self.assertEqual(
            normalize_wikimedia_img_url(f"{self.base}/a/ab/Scan.tif?utm_source=x"),
            f"{self.base}/a/ab/Scan.tif",
        )
        self.assertEqual(
            normalize_wikimedia_img_url(f"{self.base}/Scan.jpg?utm_source=x"),
            f"{self.base}/Scan.jpg",
        )
        self.assertEqual(
            normalize_wikimedia_img_url(f"{self.base}/a/ab/Scan?utm_source=x"),
            f"{self.base}/a/ab/Scan",
        )

    def test_empty_url(self):
        self.assertEqual(normalize_wikimedia_img_url(""), "")


def _statement(name, rank="normal"):
    return {"rank": rank, "mainsnak": {"datavalue": {"value": name}}}


class WikidataImageRankTestCase(SimpleTestCase):
    def test_preferred_wins(self):
        claims = [_statement("a.jpg"), _statement("b.jpg", "preferred")]
        self.assertEqual(pick_wikidata_image_name(claims), "b.jpg")

    def test_first_of_normal_rank(self):
        claims = [_statement("a.jpg"), _statement("b.jpg")]
        self.assertEqual(pick_wikidata_image_name(claims), "a.jpg")

    def test_deprecated_is_ignored(self):
        claims = [_statement("a.jpg", "deprecated"), _statement("b.jpg")]
        self.assertEqual(pick_wikidata_image_name(claims), "b.jpg")

    def test_no_usable_statement(self):
        self.assertIsNone(pick_wikidata_image_name([]))
        self.assertIsNone(pick_wikidata_image_name([_statement("a.jpg", "deprecated")]))
        self.assertIsNone(
            pick_wikidata_image_name([{"rank": "normal", "mainsnak": {}}])
        )

    @mock.patch("apis_core.apis_metainfo.models.requests.get")
    def test_fetch_image_uses_preferred_image(self, get):
        claims = {
            "claims": {"P18": [_statement("a.jpg"), _statement("b.jpg", "preferred")]}
        }
        thumb = "https://upload.wikimedia.org/wikipedia/commons/thumb/x/xy/b.jpg/250px-b.jpg"
        pages = {"query": {"pages": {"1": {"imageinfo": [{"thumburl": thumb}]}}}}
        get.side_effect = [
            mock.Mock(status_code=200, json=lambda: claims),
            mock.Mock(status_code=200, json=lambda: pages),
        ]
        self.assertEqual(fetch_image("http://www.wikidata.org/entity/Q1"), thumb)
        self.assertIn("titles=File:b.jpg", get.call_args_list[1].args[0])

    @mock.patch("apis_core.apis_metainfo.models.requests.get")
    def test_fetch_image_without_image(self, get):
        get.return_value = mock.Mock(status_code=200, json=lambda: {"claims": {}})
        self.assertEqual(fetch_image("Q1"), "")

    @mock.patch("apis_core.apis_metainfo.models.time.sleep")
    @mock.patch("apis_core.apis_metainfo.models.requests.get")
    def test_fetch_image_retries_on_too_many_requests(self, get, sleep):
        limited = mock.Mock(status_code=429, headers={"Retry-After": "1"})
        ok = mock.Mock(status_code=200, json=lambda: {"claims": {}})
        get.side_effect = [limited, ok]
        self.assertEqual(fetch_image("Q1"), "")
        self.assertEqual(get.call_count, 2)
        sleep.assert_called_once_with(1)

    @mock.patch("apis_core.apis_metainfo.models.time.sleep")
    @mock.patch("apis_core.apis_metainfo.models.requests.get")
    def test_fetch_image_raises_if_rate_limit_persists(self, get, sleep):
        limited = mock.Mock(status_code=429, headers={})
        limited.raise_for_status.side_effect = requests.HTTPError("429")
        get.return_value = limited
        with self.assertRaises(requests.HTTPError):
            fetch_image("Q1")
        self.assertEqual(get.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    @mock.patch("apis_core.apis_metainfo.models.requests.get")
    def test_fetch_image_without_thumbnail_info(self, get):
        claims = {"claims": {"P18": [_statement("b b.jpg")]}}
        get.side_effect = [
            mock.Mock(status_code=200, json=lambda: claims),
            mock.Mock(
                status_code=200,
                json=lambda: {"query": {"pages": {"-1": {"missing": ""}}}},
            ),
        ]
        self.assertEqual(
            fetch_image("Q1"),
            "https://commons.wikimedia.org/w/index.php?title=Special:Redirect/file/b%20b.jpg",
        )


class FetchImagesCommandTestCase(TestCase):
    def _entity(self, model, name, wikidata_id, **kwargs):
        entity = model.objects.create(name=name, **kwargs)
        Uri.objects.create(
            uri=f"http://www.wikidata.org/entity/{wikidata_id}",
            domain="wikidata",
            entity=entity,
        )
        return entity

    @mock.patch("apis_core.apis_entities.management.commands.fetch_images.write_report")
    @mock.patch("apis_core.apis_entities.management.commands.fetch_images.time.sleep")
    @mock.patch("apis_core.apis_metainfo.models.fetch_image")
    def test_queue(self, fetch, sleep, report):
        from datetime import timedelta

        from django.core.management import call_command
        from django.utils import timezone

        thumb = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/x.jpg/250px-x.jpg"
        fetch.side_effect = lambda uri: thumb if uri.endswith("Q3") else ""
        no_image = self._entity(Person, "ohne Bild", "Q1")
        no_image.refresh_from_db()
        work = self._entity(Work, "Werk", "Q3")
        # checked recently without result: skipped
        recent = self._entity(Person, "kürzlich", "Q2")
        Person.objects.filter(pk=recent.pk).update(img_last_checked=timezone.now())
        # checked long ago without result: checked again
        old = self._entity(Person, "alt", "Q4")
        Person.objects.filter(pk=old.pk).update(
            img_last_checked=timezone.now() - timedelta(days=60)
        )

        call_command("fetch_images")

        self.assertEqual(
            sorted(c.args[0][-2:] for c in fetch.call_args_list), ["Q1", "Q3", "Q4"]
        )
        work.refresh_from_db()
        self.assertEqual(work.img_url, thumb)
        # an entity without image keeps its check date, so it leaves the queue
        no_image.refresh_from_db()
        self.assertIsNone(no_image.img_url)
        self.assertIsNotNone(no_image.img_last_checked)
        fetch.reset_mock()
        call_command("fetch_images")
        fetch.assert_not_called()


class UriListViewTestCase(TestCase):
    """The URI list has more than 600,000 rows in production (#558)."""

    @classmethod
    def setUpTestData(cls):
        # post_save gives every entity its default PMB URI (domain "pmb")
        cls.entities = [
            Person.objects.create(name="Schnitzler", first_name="Arthur"),
            Place.objects.create(name="Wien"),
            Institution.objects.create(name="Burgtheater"),
            Event.objects.create(name="Premiere"),
            Work.objects.create(name="Reigen"),
        ]
        Uri.objects.bulk_create(
            Uri(uri=f"https://example.org/{i}", domain="example") for i in range(300)
        )
        cls.url = reverse("apis_core:apis_metainfo:uri_browse")

    def test_counts_once_and_needs_no_queries_per_row(self):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        sqls = [q["sql"] for q in ctx.captured_queries]
        # one COUNT for the paginator and one query for the page itself
        self.assertEqual(len(sqls), 2, sqls)
        self.assertEqual(sum("COUNT(" in sql for sql in sqls), 1, sqls)
        self.assertFalse(any("DISTINCT" in sql for sql in sqls), sqls)

    def test_links_to_entity_detail_views(self):
        response = self.client.get(self.url, {"domain": "pmb"})
        for entity in self.entities:
            self.assertContains(response, f"href='{entity.get_absolute_url()}'")

    def test_export_has_plain_entity_names(self):
        response = self.client.get(self.url, {"domain": "pmb", "_export": "csv"})
        content = response.content.decode()
        self.assertIn(f"Reigen (ID: {self.entities[-1].id})", content)
        self.assertNotIn("<a ", content)

    def test_goto_page_is_a_number_field(self):
        # 300 URIs in domain "example" make 12 pages
        response = self.client.get(self.url, {"domain": "example", "page": 2})
        self.assertContains(response, 'type="number"')
        self.assertContains(response, 'max="12"')
        self.assertContains(
            response, '<input type="hidden" name="domain" value="example">'
        )
        self.assertNotContains(response, '<input type="hidden" name="page"')
        self.assertNotContains(response, '<option value="?')

    def test_shows_entity_type_column(self):
        response = self.client.get(self.url, {"domain": "pmb", "columns": "ent_type"})
        self.assertEqual(response.status_code, 200)
        ent_types = {
            row.get_cell("ent_type") for row in response.context["table"].rows
        }
        self.assertEqual(
            ent_types, {"Person", "Place", "Institution", "Event", "Work"}
        )

    def test_entity_without_child_is_plain_text(self):
        # a bare TempEntityClass has no Person/Place/… behind it
        orphan = TempEntityClass.objects.create(name="Waise")
        uri = Uri.objects.create(uri="https://example.org/orphan", entity=orphan)
        table = UriTable([uri])
        self.assertEqual(table.render_entity(orphan), str(orphan))
        self.assertEqual(table.render_ent_type(uri), "")

class UriLinkUrlTestCase(SimpleTestCase):
    def test_anno_fragment_is_cut_off(self):
        uri = Uri(
            uri="https://anno.onb.ac.at/cgi-content/anno?aid=bth&datum=19000127&seite=1#burgtheater-die-damen-lebardieu"
        )
        self.assertEqual(
            uri.get_link_url(),
            "https://anno.onb.ac.at/cgi-content/anno?aid=bth&datum=19000127&seite=1",
        )
        self.assertIn("#burgtheater-die-damen-lebardieu", str(uri))

    def test_other_uris_are_unchanged(self):
        for value in [
            "https://anno.onb.ac.at/cgi-content/anno?aid=bth&datum=19000127&seite=1",
            "https://example.org/entity#fragment",
            "https://d-nb.info/gnd/118609807",
        ]:
            self.assertEqual(Uri(uri=value).get_link_url(), value)

    def test_empty_uri(self):
        self.assertEqual(Uri(uri=None).get_link_url(), "")
