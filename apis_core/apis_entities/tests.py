from AcdhArcheAssets.uri_norm_rules import get_normalized_uri
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from icecream import ic

from apis_core.apis_entities.forms import get_entities_form
from apis_core.apis_entities.models import Person, Place
from apis_core.helper_functions.DateParser import parse_date
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

        url = reverse("entity-resolver", kwargs={"pk": 11})
        r = client.get(f"{url}?format=tei")
        self.assertEqual(r.status_code, 302)

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

    def test_009a_merge_notesandreferences_andgedner(self):
        source_one = Person.objects.create(
            name="Person which will be merged",
            notes="notes_one",
            references="references_one",
            gender="female",
        )
        source_two = Person.objects.create(
            name="Person two which will be merged", gender="male"
        )
        target = Person.objects.create(
            name="Person which will be kept",
            notes="target_notes",
            references="target_references",
        )
        target.merge_with(source_one.id)
        self.assertEqual("female", target.gender)
        self.assertTrue("notes_one" in target.notes)
        self.assertTrue("target_notes" in target.notes)
        self.assertTrue("references_one" in target.references)
        self.assertTrue("target_references" in target.references)
        target.merge_with(source_two)
        self.assertEqual("female", target.gender)

        place_target = Place.objects.create(name="Sumsi")
        place_source = Place.objects.create(name="Dumsi")
        place_target.merge_with(place_source.id)

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

    def test_017_import_institution(self):
        client.login(**USER)
        payload = {
            "normdata_url": "https://d-nb.info/gnd/414136-2",
            "entity_type": "institution",
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
                r = client.get(f"{value}?format=json%2Bnet")
                self.assertTrue(r.status_code, 200)

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

    def test_023_save_uris(self):
        wd_uri = "https://www.wikidata.org/wiki/Q2"
        entity = Person.objects.last()
        new_uri = Uri.objects.create(uri=wd_uri, entity=entity)
        self.assertEqual(new_uri.uri, get_normalized_uri(wd_uri))

    def test_024_autocompletes(self):
        models = ["person", "place", "event", "institution", "work"]
        for x in models:
            url = reverse(
                "apis:apis_entities:generic_entities_autocomplete", kwargs={"entity": x}
            )
            r = client.get(f"{url}?q=a")
            self.assertEqual(r.status_code, 200)

    def test_024_vocabs_dl(self):
        models = ["placetype", "worktype"]
        client.login(**USER)
        for x in models:
            url = reverse("apis:apis_vocabularies:dl-vocabs", kwargs={"model_name": x})
            r = client.get(f"{url}")
            self.assertEqual(r.status_code, 200)

    def test_025_vocabs_ac(self):
        models = ["placetype", "worktype", "personplacerelation", "personworkrelation"]
        client = Client()
        for x in models:
            for y in ["normal", "reverse"]:
                if y == "reverse" and x.endswith("type"):
                    continue
                r = None
                url = reverse(
                    "apis:apis_vocabularies:generic_vocabularies_autocomplete",
                    kwargs={"vocab": x, "direct": y},
                )
                r = client.get(f"{url}")
                self.assertEqual(r.status_code, 200)
                r = client.get(f"{url}?q=g")
                self.assertEqual(r.status_code, 200)

    def test_026_fetch_image(self):
        grillparzer = "https://d-nb.info/gnd/118542192"
        entity = import_from_normdata(grillparzer, "person")
        entity.fetch_image()
        self.assertTrue(entity.img_url)
        self.assertTrue("Wikimedia Commons" in entity.img_credit_label())
        self.assertTrue("File:" in entity.img_credit())

    def test_027_img_credit(self):
        entity = import_from_normdata("https://www.wikidata.org/wiki/Q76483", "person")
        self.assertIsNone(entity.img_credit())
        self.assertIsNone(entity.img_credit_label())

    def test_028_beacons(self):
        url = reverse("apis_core:beacon")
        r = client.get(url)
        self.assertEqual(r.status_code, 200)
        url = reverse("apis_core:wikidata_beacon")
        r = client.get(url)
        self.assertEqual(r.status_code, 200)

    def test_029_parse_date(self):
        dates = [
            ["1900", ["1900-01-01", "1900-01-01", "1900-12-31"]],
            ["1800-02", ["1800-02-01", "1800-02-01", "1800-02-28"]],
            ["1800-02-02", ["1800-02-02", "None", "None"]],
            ["um 1900<1900-03-03>", ["1900-03-03", "None", "None"]],
        ]
        for x in dates:
            results = parse_date(x[0])
            for i, r in enumerate(results):
                date_str = f"{r}"[:10]
                self.assertEqual(date_str, x[1][i])

    def test_030_clean_written_dates(self):
        item = Person.objects.create(
            start_date_written="1800<1812-01-04>", end_date_written="um 1900"
        )
        self.assertFalse("<" in item.clean_start_date_written())
        self.assertFalse("<" in item.clean_end_date_written())
        self.assertTrue("<" in item.start_date_written)
        self.assertFalse("<" in item.end_date_written)

    def test_031_get_colo(self):
        DEFAULT_COLOR = settings.DEFAULT_COLOR
        DOMAIN_MAPPING = settings.DOMAIN_MAPPING
        item = Person.objects.create(name="hansi4ever")
        for x in DOMAIN_MAPPING[:3]:
            uri = Uri.objects.create(
                uri=f"https://{x[0]}/sumsi.com", domain=x[1], entity=item
            )
            self.assertEqual(uri.get_color(), x[2])
        uri = Uri.objects.create(
            uri="https://whatdoicare/123.at", domain="somethingveryrandom", entity=item
        )
        self.assertEqual(uri.get_color(), DEFAULT_COLOR)
