from django.apps import apps
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from apis_core.apis_entities.forms import get_entities_form
from apis_core.apis_entities.models import Person
from apis_core.apis_metainfo.models import Uri
from normdata.forms import NormDataImportForm

client = Client()
USER = {"username": "testuser", "password": "somepassword"}
BAHR = {"name": "Bahr", "first_name": "Hermann", "start_date_written": "1900"}
DUMMY_OBJECT = {"name": "test", "start_date_written": "1900"}

ENTITY_TYPES = ["person", "place", "event", "work", "institution"]

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
        for x in ENTITY_TYPES:
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

    def test_010_delete_views(self):
        client.login(**USER)
        for x in MODELS:
            entity_type = f"{x.__name__.lower()}"
            if entity_type in ENTITY_TYPES:
                try:
                    item, created = x.objects.get_or_create(**DUMMY_OBJECT)
                except Exception:
                    item = x.objects.filter(name="test").first()
                url = reverse(
                    "apis:apis_entities:generic_entities_delete_view",
                    kwargs={"entity": f"{x.__name__.lower()}", "pk": item.id},
                )
                item.save()
                response = client.get(url)
                self.assertContains(response, "Löschen von")
                self.assertContains(response, item.id)
                item.delete()

    def test_010_import_nordmdata_view(self):
        client.login(**USER)
        payload = {
            "normdata_url": "http://lobid.org/gnd/118566512",
            "entity_type": "person",
        }
        url = reverse(
            "normdata:import_from_normdata",
        )
        response = client.post(url, payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Uri.objects.filter(uri__icontains="118566512"))
        payload = {
            "normdata_url": "https://www.geonames.org/2772400/linz.html",
            "entity_type": "place",
        }
        response = client.post(url, payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Uri.objects.filter(uri__icontains="2772400"))

        payload = {
            "normdata_url": "https://www.wikidata.org/wiki/Q119350694",
            "entity_type": "person",
        }
        response = client.post(url, payload, follow=True)
        self.assertEqual(response.status_code, 200)

        payload = {
            "normdata_url": "https://www.wikidata.org/wiki/Q119350694",
            "entity_type": "person",
        }
        response = client.post(url, payload, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_011_import_normdata_form(self):
        payload = {
            "normdata_url": "http://lobid.org/gnd/118566512",
            "entity_type": "person",
        }
        form = NormDataImportForm(data=payload)
        self.assertTrue(form.is_valid())
