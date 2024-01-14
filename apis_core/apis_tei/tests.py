from django.apps import apps
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from apis_core.apis_entities.models import Person

client = Client()
USER = {"username": "testuser", "password": "somepassword"}
BAHR = {"name": "Bahr", "first_name": "Hermann", "start_date_written": "1900"}
DUMMY_OBJECT = {"name": "test", "start_date_written": "1900"}

ENTITY_TYPES = ["person", "place", "event", "work", "institution"]

MODELS = list(apps.all_models["apis_entities"].values())


class TeiTestCase(TestCase):
    fixtures = [
        "db.json",
    ]

    def setUp(self):
        User.objects.create_user(**USER)
        Person.objects.create(**BAHR)

    def test_01_tei_autocomplete(self):
        url = reverse(
            "apis:apis_tei:generic_entities_autocomplete", kwargs={"entity": "person"}
        )
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        response = client.get(f"{url}?q=Bahr")
        self.assertTrue("Hermann" in str(response.content))

    def test_02_tei_completer_autocomplete(self):
        url = reverse(
            "apis:apis_tei:tei_completer_autocomplete", kwargs={"entity": "person"}
        )
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        response = client.get(f"{url}?q=Bahr")
        self.assertTrue("Hermann" in str(response.content))

    def test_03_tei_views(self):
        for x in MODELS:
            item = x.objects.first()
            try:
                url = item.get_tei_url()
            except AttributeError:
                url = False
            if url:
                try:
                    response = client.get(url)
                except TypeError:
                    continue
                self.assertEqual(response.status_code, 200)
