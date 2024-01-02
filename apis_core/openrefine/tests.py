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


class OpenrefineTestCase(TestCase):
    def setUp(self):
        # Create two users
        User.objects.create_user(**USER)
        Person.objects.create(**BAHR)

    def test_01_tei_reconcile(self):
        url = reverse("apis:openrefine:reconcile")
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        response = client.post(url)
        self.assertEqual(response.status_code, 200)

    def test_02_properties(self):
        url = reverse("apis:openrefine:properties")
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_03_suggest_types(self):
        url = reverse("apis:openrefine:suggest_types")
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
