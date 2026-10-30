# Create your tests here.

from unittest import mock

import requests
from django.apps import apps
from django.contrib.auth.models import User
from django.test import Client, SimpleTestCase, TestCase

from apis_core.apis_entities.models import Person, Work
from apis_core.apis_metainfo.models import (
    Collection,
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
        url = f"{self.base}/thumb/4/40/Hermann_Bahr_1891.jpg/250px-Hermann_Bahr_1891.jpg"
        self.assertEqual(normalize_wikimedia_img_url(url), url)

    def test_svg_gets_png_suffix(self):
        self.assertEqual(
            normalize_wikimedia_img_url(f"{self.base}/a/ab/Wappen.svg"),
            f"{self.base}/thumb/a/ab/Wappen.svg/250px-Wappen.svg.png",
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
            mock.Mock(status_code=200, json=lambda: {"query": {"pages": {"-1": {"missing": ""}}}}),
        ]
        self.assertEqual(
            fetch_image("Q1"),
            "https://commons.wikimedia.org/w/index.php?title=Special:Redirect/file/b%20b.jpg",
        )
