from django.test import TestCase

from normdata.utils import get_or_create_place_from_geonames

GEONAMES_URL = "https://www.geonames.org/2461464/graret-oum-sedra.html"


class NormdataTestCase(TestCase):
    def test_001_get_or_create_place_from_geonames(self):
        entity = get_or_create_place_from_geonames(GEONAMES_URL)
        self.assertEqual(entity.name, "Graret Oum Sedra")
        entity = get_or_create_place_from_geonames(GEONAMES_URL)
        entity.delete()
