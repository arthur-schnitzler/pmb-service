from django.apps import apps
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from apis_core.apis_entities.models import Person
from apis_core.apis_entities.forms import get_entities_form

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

    def test_005_check_fixtures(self):
        items = Person.objects.all().count()
        self.assertEqual(items, 2)

    def test_006_create_person(self):
        item, created = Person.objects.get_or_create(**BAHR)
        self.assertTrue(created)
        self.assertEqual(item.name, "Bahr")

    def test_007_delete_person(self):
        item, _ = Person.objects.get_or_create(**BAHR)
        self.assertEqual(item.name, "Bahr")
        item.delete()

    def test_008_get_entities_form(self):
        for x in ["person", "place", "event", "work", "institution"]:
            data = {"name": f"{x}__hansi", "start_date_written": "1900"}
            form_class = get_entities_form(x.title())
            form = form_class(data=data)
            self.assertTrue(form.is_valid())
            created_object = form.save()
            self.assertTrue(created_object.id > 0)

    def test_009_merge_view(self):
        client.login(**USER)
        before = Person.objects.all().count()
        source = Person.objects.all().first()
        target = Person.objects.all().last()
        target_uri = target.uri_set.all().first()
        form_kwargs = {"entity": "person"}
        form_kwargs["ent_merge_pk"] = source.id
        url = reverse(
            "apis:apis_entities:merge_view",
            kwargs={"entity": "person", "ent_merge_pk": source.id},
        )
        response = client.post(url, {"entity": target_uri})
        self.assertEqual(response.status_code, 302)
        after = Person.objects.all().count()
        self.assertTrue(before > after)
