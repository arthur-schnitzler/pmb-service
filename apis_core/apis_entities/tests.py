# from django.apps import apps
from django.test import TestCase, Client
from django.contrib.auth.models import User

from apis_core.apis_entities.models import Person


client = Client()
USER = {"username": "testuser", "password": "somepassword"}
BAHR = {"name": "Bahr", "first_name": "Hermann", "start_date_written": "1900"}


class EntitiesTestCase(TestCase):
    fixtures = [
        "db.json",
    ]

    def setUp(self):
        # Create two users
        User.objects.create_user(**USER)

    def test_001_person_list_view(self):
        url = Person.get_listview_url()
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_002_check_fixtures(self):
        items = Person.objects.all().count()
        self.assertEqual(items, 2)

    def test_003_create_person(self):
        item, created = Person.objects.get_or_create(**BAHR)
        self.assertTrue(created)
        self.assertEqual(item.name, "Bahr")

    def test_004_delete_person(self):
        item, _ = Person.objects.get_or_create(**BAHR)
        self.assertEqual(item.name, "Bahr")
        item.delete()
