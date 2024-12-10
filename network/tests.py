from django.apps import apps
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse


client = Client()
USER = {"username": "testuser", "password": "password", "is_active": True}
BAHR = {"name": "Schnitzler", "first_name": "Hermann", "start_date_written": "1900"}

ENTITY_TYPES = ["person", "place", "event", "work", "institution"]

MODELS = list(apps.all_models["apis_entities"].values())
MEDIA_ROOT = settings.MEDIA_ROOT


class DumperTestCase(TestCase):
    fixtures = [
        "network.json",
    ]

    def test_01_network(self):
        url = reverse("network:network")
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
        url = reverse("network:map")
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
