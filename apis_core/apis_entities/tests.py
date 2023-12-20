from django.apps import apps
from django.test import TestCase, Client
from django.contrib.auth.models import User

from apis_core.apis_entities.models import Person


client = Client()
USER = {"username": "testuser", "password": "somepassword"}
BAHR = {"name": "Bahr", "first_name": "Hermann", "start_date_written": "1900"}

MODELS = list(apps.all_models["apis_entities"].values())


class EntitiesTestCase(TestCase):
    fixtures = [
        "db.json",
    ]

    def setUp(self):
        # Create two users
        User.objects.create_user(**USER)

    def test_001_list_view(self):
        for x in MODELS:
            try:
                url = x.get_listview_url()
            except AttributeError:
                url = False
            if url:
                response = client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_002_detailviews(self):
        for x in MODELS:
            item = x.objects.first()
            try:
                url = item.get_absolute_url()
            except AttributeError:
                url = False
            if url:
                response = client.get(url, {"pk": item.id})
                self.assertEqual(response.status_code, 200)

    def test_003_editviews(self):
        client.login(**USER)
        for x in MODELS:
            item = x.objects.first()
            try:
                url = item.get_edit_url()
            except AttributeError:
                url = False
            if url:
                response = client.get(url, {"pk": item.id})
                self.assertEqual(response.status_code, 200)

    def test_004_createviews_logged_in(self):
        client.login(**USER)
        for x in MODELS:
            item = x.objects.first()
            try:
                url = item.get_createview_url()
            except AttributeError:
                url = False
            if url:
                response = client.get(url, {"pk": item.id})
                self.assertEqual(response.status_code, 200)

    def test_004_check_fixtures(self):
        items = Person.objects.all().count()
        self.assertEqual(items, 2)

    def test_005_create_person(self):
        item, created = Person.objects.get_or_create(**BAHR)
        self.assertTrue(created)
        self.assertEqual(item.name, "Bahr")

    def test_006_delete_person(self):
        item, _ = Person.objects.get_or_create(**BAHR)
        self.assertEqual(item.name, "Bahr")
        item.delete()
