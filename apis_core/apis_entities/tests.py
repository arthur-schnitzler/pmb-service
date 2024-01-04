from django.apps import apps
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from icecream import ic

from apis_core.apis_entities.forms import get_entities_form
from apis_core.apis_entities.models import Person, Place
from apis_core.apis_metainfo.models import Uri
from normdata.forms import NormDataImportForm
from normdata.utils import (
    get_or_create_person_from_wikidata,
    get_or_create_place_from_wikidata,
    import_from_normdata,
)

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
        User.objects.create_user(**USER)

    def test_001a_entity_resolver(self):
        url = reverse("entity-resolver", kwargs={"pk": 4})
        r = client.get(url)
        self.assertEqual(r.status_code, 404)

        url = reverse("entity-resolver", kwargs={"pk": 44442344})
        r = client.get(url)
        self.assertEqual(r.status_code, 404)

        url = reverse("entity-resolver", kwargs={"pk": 1})
        r = client.get(url)
        self.assertEqual(r.status_code, 302)

        url = reverse("entity-resolver", kwargs={"pk": 1})
        r = client.get(f"{url}?format=tei")
        self.assertEqual(r.status_code, 302)

        url = reverse("entity-resolver", kwargs={"pk": 1})
        r = client.get(f"{url}?format=json")
        self.assertEqual(r.status_code, 302)

        url = reverse("entity-resolver", kwargs={"pk": 1})
        r = client.get(f"{url}?format=asdf")
        self.assertEqual(r.status_code, 404)

        url = reverse("entity-resolver", kwargs={"pk": 9})
        r = client.get(f"{url}?format=tei")
        self.assertEqual(r.status_code, 404)

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
        form_kwargs = {"entity": "person"}
        form_kwargs["ent_merge_pk"] = source.id
        url = reverse(
            "apis:apis_entities:merge_view",
            kwargs={"entity": "person", "ent_merge_pk": source.id},
        )
        response = client.post(url, {"entity": target.id})
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

    def test_011_import_nordmdata_view(self):
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

    def test_012_import_normdata_form(self):
        payload = {
            "normdata_url": "http://lobid.org/gnd/118566512",
            "entity_type": "person",
        }
        form = NormDataImportForm(data=payload)
        self.assertTrue(form.is_valid())

    def test_013_import_normdata_no_wikidata(self):
        client.login(**USER)
        payload = {
            "normdata_url": "https://www.geonames.org/2461492/graret-um-igufen.html",
            "entity_type": "person",
        }
        url = reverse(
            "normdata:import_from_normdata",
        )
        response = client.post(url, payload, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_014_wikidata_place_exist(self):
        entity = get_or_create_place_from_wikidata(
            "http://www.wikidata.org/entity/Q1741"
        )
        ic(entity)
        for x in entity.uri_set.all():
            entity = get_or_create_place_from_wikidata(x.uri)
            self.assertTrue(entity)

    def test_015_wikidata_person_exist(self):
        entity = import_from_normdata("http://lobid.org/gnd/133430553", "person")
        for x in entity.uri_set.all():
            entity = get_or_create_person_from_wikidata(x.uri)
            self.assertTrue(entity)

    def test_016_import_nonsense_geonames(self):
        client.login(**USER)
        payload = {
            "normdata_url": "https://www.geonames.org/2461123321492/graret-um-igufen.html",
            "entity_type": "place",
        }
        url = reverse(
            "normdata:import_from_normdata",
        )
        response = client.post(url, payload, follow=True)
        self.assertEqual(response.status_code, 404)

    def test_017_import_gndplacewithoutwikidata(self):
        client.login(**USER)
        payload = {
            "normdata_url": "https://d-nb.info/gnd/10053010-2",
            "entity_type": "place",
        }
        url = reverse(
            "normdata:import_from_normdata",
        )
        response = client.post(url, payload, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_017_import_gndpersonwithoutwikidata(self):
        client.login(**USER)
        payload = {
            "normdata_url": "https://d-nb.info/gnd/1168743451",
            "entity_type": "person",
        }
        url = reverse(
            "normdata:import_from_normdata",
        )
        response = client.post(url, payload, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_018_download_vocabs(self):
        model_name = "worktype"
        url = reverse(
            "apis_core:apis_vocabularies:dl-vocabs", kwargs={"model_name": model_name}
        )
        client.login(**USER)
        response = client.get(url, follow=True)
        content_disposition = response.headers["Content-Disposition"]
        self.assertTrue(model_name in content_disposition)

    def test_019_download_vocabs_not_exist(self):
        model_name = "doesnotexistworktype"
        url = reverse(
            "apis_core:apis_vocabularies:dl-vocabs", kwargs={"model_name": model_name}
        )
        client.login(**USER)
        response = client.get(url, follow=True)
        self.assertTrue(response.status_code, 404)

    def test_020_api_list_view(self):
        url = "/apis/api/"
        response = client.get(url, follow=True)
        self.assertTrue(response.status_code, 200)
        data = response.json()
        for key, value in data.items():
            r = client.get(value)
            self.assertTrue(r.status_code, 200)
            if key.startswith("relation"):
                try:
                    r = client.get(f"{value}?format=json%2Bnet")
                    self.assertTrue(r.status_code, 200)
                except Exception as e:
                    print(value, e)
                    continue

    def test_021_api_detail_view(self):
        item = Person.objects.last()
        r = client.get(item.get_api_url())
        self.assertTrue(r.status_code, 200)
        item = Place.objects.last()
        r = client.get(item.get_api_url())
        self.assertTrue(r.status_code, 200)

    def test_022_resolver_view(self):
        target = Person.objects.last()
        source = Person.objects.create(**{"name": "wirdgleichgemerged"})
        source_id = source.id
        source_uri = f"https://pmb.acdh.oeaw.ac.at/entity/{source.id}/"
        target.merge_with(source_id)
        url = reverse("uri-resolver")
        r = client.get(url)
        self.assertTrue(r.status_code, 404)
        r = client.get(f"{url}?uri={source_uri}")
        self.assertTrue(r.status_code, 302)
        r = client.get(f"{url}?uri={source_uri}&format=tei")
        self.assertTrue(r.status_code, 302)
        r = client.get(f"{url}?uri={source_uri}&format=json")
        self.assertTrue(r.status_code, 302)
        r = client.get(f"{url}?uri={source_uri}&format=nonsense")
        self.assertTrue(r.status_code, 404)
        r = client.get(f"{url}?uri=https://dasgibtsjagarnicht.com")
        self.assertTrue(r.status_code, 404)
