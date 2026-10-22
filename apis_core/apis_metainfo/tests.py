# Create your tests here.

from django.apps import apps
from django.contrib.auth.models import User
from django.test import Client, TestCase

from apis_core.apis_entities.models import Person, Work
from apis_core.apis_metainfo.models import (
    Collection,
    Uri,
    normalize_wikimedia_img_url,
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
