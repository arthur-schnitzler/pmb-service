from django.test import TestCase
from pylobid.pylobid import PyLobidPerson
from normdata.utils import (
    get_gender_from_pylobid,
    get_or_create_person_from_gnd,
    get_or_create_place_from_geonames,
    get_or_create_place_from_gnd,
    get_or_create_org_from_wikidata,
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

    def test_002_get_or_create_place_from_gnd_no_coords(self):
        entity = get_or_create_place_from_gnd("http://lobid.org/gnd/10053010-2")
        self.assertEqual(entity.name, "Horco Molle")
        entity = get_or_create_place_from_gnd("http://lobid.org/gnd/10053010-2")
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
