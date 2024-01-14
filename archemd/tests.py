from django.apps import apps
from django.test import Client, TestCase
from django.urls import reverse

from apis_core.apis_entities.models import Person, Place
from archemd.arche_md_utils import ArcheMd

client = Client()
USER = {"username": "testuser", "password": "somepassword"}
BAHR = {"name": "Bahr", "first_name": "Hermann", "start_date_written": "1900"}

ENTITY_TYPES = ["person", "place", "event", "work", "institution"]

MODELS = list(apps.all_models["apis_entities"].values())

URIS = [
    ("https://www.geonames.org/2772400/linz.html", "place"),
    ("https://www.wikidata.org/wiki/Q100965214", "person"),
    ("http://lobid.org/gnd/1028192029", "person"),
]


class ArcheMedTestCase(TestCase):
    fixtures = [
        "db.json",
    ]

    def test_01_archemd(self):
        item = Person.objects.last()
        arche_md = ArcheMd(item.id)
        g = arche_md.return_graph()
        self.assertTrue(g)

    def test_02_archemd_view(self):
        for item in Person.objects.all():
            url = reverse("archemd:arche", kwargs={"pk": item.id})
            response = client.get(url)
            self.assertTrue(response.status_code, 200)
        for item in Place.objects.all():
            url = reverse("archemd:arche", kwargs={"pk": item.id})
            response = client.get(url)
            self.assertTrue(response.status_code, 200)

    def test_03_archemd_doesnotexist(self):
        url = reverse("archemd:arche", kwargs={"pk": 99999})
        response = client.get(url)
        self.assertTrue(response.status_code, 404)
