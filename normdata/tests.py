from unittest import mock

from acdh_wikidata_pyutils import WikiDataPlace
from AcdhArcheAssets.uri_norm_rules import get_normalized_uri
from django.test import TestCase
from pylobid.pylobid import PyLobidPerson

from apis_core.apis_entities.models import Institution, Person, Place
from apis_core.apis_metainfo.models import Uri
from normdata.utils import (
    fetch_image_safely,
    get_gender_from_pylobid,
    get_or_create_org_from_wikidata,
    get_or_create_person_from_gnd,
    get_or_create_place_from_geonames,
    get_or_create_place_from_gnd,
    get_or_create_place_from_wikidata,
    import_from_normdata,
)

GEONAMES_URL = "https://www.geonames.org/2461464/graret-oum-sedra.html"
GND_URL = "http://lobid.org/gnd/4547867-3"
FEMALE_GND = "https://d-nb.info/gnd/128348623"
MALE_GND = "https://d-nb.info/gnd/136390307"
NO_GENDER = "https://d-nb.info/gnd/1168743451"


class NormdataTestCase(TestCase):
    def test_001_get_or_create_place_from_geonames(self):
        entity = get_or_create_place_from_geonames(GEONAMES_URL)
        self.assertEqual(entity.name, "Graret Oum Sedra")
        entity = get_or_create_place_from_geonames(GEONAMES_URL)
        entity.delete()

    def test_002_get_or_create_place_from_gnd(self):
        entity = get_or_create_place_from_gnd(GND_URL)
        self.assertEqual(entity.name, "Gramastetten")
        entity = get_or_create_place_from_gnd(GND_URL)
        entity.delete()

    def test_002a_get_or_create_place_from_gnd_no_coords(self):
        entity = get_or_create_place_from_gnd("http://lobid.org/gnd/1121703259")
        self.assertEqual(entity.name, "Dobrova", msg=f"should be {entity.name}")
        entity = get_or_create_place_from_gnd("http://lobid.org/gnd/1121703259")
        entity.delete()

    def test_003_get_gender_from_pylobid(self):
        fetched_entity = PyLobidPerson(FEMALE_GND)
        gender = get_gender_from_pylobid(fetched_entity)
        self.assertEqual("female", gender)
        fetched_entity = PyLobidPerson(MALE_GND)
        gender = get_gender_from_pylobid(fetched_entity)
        self.assertEqual("male", gender)
        fetched_entity = PyLobidPerson(NO_GENDER)
        gender = get_gender_from_pylobid(fetched_entity)
        self.assertEqual(None, gender)

    def test_004_get_or_create_person_from_gnd(self):
        gender = ["female", "male", None]
        for i, x in enumerate([FEMALE_GND, MALE_GND, NO_GENDER]):
            entity = get_or_create_person_from_gnd(x)
            gnd_uri = entity.uri_set.filter(uri__icontains=x)
            self.assertEqual(gnd_uri.count(), 1)
            self.assertEqual(entity.gender, gender[i])
        entity = get_or_create_person_from_gnd(x)

    def test_005_get_or_create_org_from_wikidata(self):
        entity = get_or_create_org_from_wikidata("https://www.wikidata.org/wiki/Q7191")
        entity = get_or_create_org_from_wikidata("https://www.wikidata.org/wiki/Q7191")
        self.assertEqual(entity.name, "Nobel Prize")

    def test_006_import_from_normdata(self):
        entity = import_from_normdata(
            "https://www.geonames.org/2516696/marisma-de-hinojos.html", "place"
        )
        self.assertTrue(entity.kind)

    def test_008_wikidata_uri_added_when_matched_via_geonames(self):
        # https://github.com/arthur-schnitzler/pmb-service/issues/231
        # Importing the "Schlossberg" (Q264176) via wikidata matches an existing
        # place by its geonames URI; the wikidata URI must still be added.
        wikidata_url = "https://www.wikidata.org/wiki/Q264176"
        wd_entity = WikiDataPlace(wikidata_url)
        place = Place.objects.create(name="Schlossberg")
        Uri.objects.create(
            uri=get_normalized_uri(wd_entity.geonames_uri),
            domain="geonames",
            entity=place,
        )
        normalized_wd = get_normalized_uri(wikidata_url)
        self.assertFalse(Uri.objects.filter(uri=normalized_wd).exists())
        entity = get_or_create_place_from_wikidata(wikidata_url)
        self.assertEqual(entity.id, place.id)
        self.assertTrue(
            Uri.objects.filter(uri=normalized_wd, entity=place).exists()
        )

    def test_007_check_for_wiengeschichte(self):
        wiengeschichte_uri = (
            "https://www.geschichtewiki.wien.gv.at/Special:URIResolver/?curid=36065"
        )
        test_uri = "https://d-nb.info/gnd/129325074"
        self.assertFalse(Uri.objects.filter(uri=wiengeschichte_uri))
        import_from_normdata(test_uri, "person")
        self.assertTrue(Uri.objects.get(uri=wiengeschichte_uri))


THUMB = "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Rilke.jpg/250px-Rilke.jpg"
WIKIDATA_IMPORTS = {
    "person": ("https://www.wikidata.org/wiki/Q76483", Person),
    "place": ("https://www.wikidata.org/wiki/Q1741", Place),
    "institution": ("https://www.wikidata.org/wiki/Q49108", Institution),
}


class ImportFetchesImageTestCase(TestCase):
    def test_import_stores_image(self):
        for entity_type, (url, model) in WIKIDATA_IMPORTS.items():
            with self.subTest(entity_type):
                with mock.patch(
                    "apis_core.apis_metainfo.models.fetch_image", return_value=THUMB
                ):
                    entity = import_from_normdata(url, entity_type)
                entity = model.objects.get(id=entity.id)
                self.assertEqual(entity.img_url, THUMB)
                self.assertIsNotNone(entity.img_last_checked)

    def test_failing_image_request_does_not_break_import(self):
        for entity_type, (url, model) in WIKIDATA_IMPORTS.items():
            with self.subTest(entity_type):
                with mock.patch(
                    "apis_core.apis_metainfo.models.fetch_image",
                    side_effect=ConnectionError("commons down"),
                ):
                    entity = import_from_normdata(url, entity_type)
                entity = model.objects.get(id=entity.id)
                self.assertIsNone(entity.img_url)
                self.assertIsNone(entity.img_last_checked)


class FetchImageSafelyTestCase(TestCase):
    def test_fetches_image(self):
        entity = mock.Mock()
        fetch_image_safely(entity)
        entity.fetch_image.assert_called_once_with()

    def test_failing_request_does_not_break_import(self):
        entity = mock.Mock()
        entity.fetch_image.side_effect = ConnectionError("commons down")
        fetch_image_safely(entity)
