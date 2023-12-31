from django.test import TestCase

from normdata.utils import (
    get_or_create_place_from_geonames,
    get_or_create_place_from_gnd,
)

GEONAMES_URL = "https://www.geonames.org/2461464/graret-oum-sedra.html"
GND_URL = "http://lobid.org/gnd/4547867-3"


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
