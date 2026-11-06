import json
from unittest import mock

from AcdhArcheAssets.uri_norm_rules import get_normalized_uri
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse
from icecream import ic

from apis_core.apis_entities.forms import get_entities_form
from apis_core.apis_entities.models import Event, Institution, Person, Place, Work
from apis_core.apis_labels.models import Label
from apis_core.apis_metainfo.errors import StartDateAfterEndDateError
from apis_core.apis_metainfo.models import Uri
from apis_core.apis_metainfo.tables import (
    written_order_end_date_written,
    written_order_start_date_written,
)
from apis_core.apis_relations.models import (
    AbstractRelation,
    PersonPerson,
    PersonPlace,
)
from apis_core.apis_vocabularies.models import (
    LabelType,
    PersonPersonRelation,
    PersonPlaceRelation,
)
from apis_core.helper_functions.DateParser import parse_date
from normdata.forms import NormDataImportForm
from normdata.utils import (
    get_or_create_person_from_wikidata,
    get_or_create_place_from_wikidata,
    get_or_create_work_from_wikidata,
    import_from_normdata,
)

client = Client()
USER = {"username": "testuser", "password": "somepassword"}
BAHR = {"name": "Bahr", "first_name": "Hermann", "start_date_written": "1900"}
DUMMY_OBJECT = {"name": "test", "start_date_written": "1900"}

ENTITY_TYPES = ["person", "place", "event", "work", "institution"]

MODELS = list(apps.all_models["apis_entities"].values())

RELATION_MODELS = list(apps.all_models["apis_relations"].values())


class EntitiesTestCase(TestCase):
    def setUp(self):
        User.objects.create_user(**USER)

    def test_001a_entity_resolver(self):
        Person.objects.get_or_create(name="Andorfer", first_name="Ronja")
        Person.objects.get_or_create(name="Andorfer", first_name="Hanna")
        url = reverse("entity-resolver", kwargs={"pk": 44442344})
        r = client.get(url)
        self.assertEqual(r.status_code, 404)
        for x in Person.objects.all():
            url = reverse("entity-resolver", kwargs={"pk": x.id})
            r = client.get(url)
            self.assertEqual(r.status_code, 302)
            r = client.get(f"{url}?format=tei")
            self.assertEqual(r.status_code, 302)
            r = client.get(f"{url}?format=json")
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

    def test_001a_relation_list_view(self):
        for x in RELATION_MODELS:
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
        Person.objects.get_or_create(name="Andorfer", first_name="Ronja")
        Person.objects.get_or_create(name="Andorfer", first_name="Hanna")
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
        target = Person.objects.create(
            name="Person which will be kept",
            notes="target_notes",
            references="target_references",
        )
        source_one = Person.objects.create(
            name="Person which will be merged",
            notes="notes_one",
            references="references_one",
            gender="female",
        )
        source_two = Person.objects.create(
            name="Person two which will be merged", gender="male"
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

    def test_009b_merge_dates(self):
        # target without lifespan inherits the dates of the merged source
        target = Person.objects.create(name="Person without dates")
        source = Person.objects.create(
            name="Person with dates",
            start_date_written="1845",
            end_date_written="1913",
        )
        target.merge_with(source.id)
        self.assertEqual("1845", target.start_date_written)
        self.assertEqual("1913", target.end_date_written)
        # the written dates are re-parsed into the structured date fields
        self.assertIsNotNone(target.start_date)
        self.assertIsNotNone(target.end_date)

        # target with its own dates keeps them, ignoring the source's dates
        target_with_dates = Person.objects.create(
            name="Person which keeps its dates",
            start_date_written="1800",
            end_date_written="1880",
        )
        source_other_dates = Person.objects.create(
            name="Person whose dates are dropped",
            start_date_written="1845",
            end_date_written="1913",
        )
        target_with_dates.merge_with(source_other_dates.id)
        self.assertEqual("1800", target_with_dates.start_date_written)
        self.assertEqual("1880", target_with_dates.end_date_written)

        # a target that already has any date keeps its lifespan untouched, so
        # mixing the target's and the source's dates can never create an
        # invalid (start-after-end) range
        target_partial = Person.objects.create(
            name="Person with only a start date",
            start_date_written="1820",
        )
        source_partial = Person.objects.create(
            name="Person whose dates are dropped",
            start_date_written="1845",
            end_date_written="1913",
        )
        target_partial.merge_with(source_partial.id)
        self.assertEqual("1820", target_partial.start_date_written)
        self.assertFalse(target_partial.end_date_written)

    def test_009c_merge_coordinates(self):
        # target without coordinates inherits them from the merged source
        target = Place.objects.create(name="Place without coordinates")
        source = Place.objects.create(
            name="Place with coordinates", lat=48.2, lng=16.37
        )
        target.merge_with(source.id)
        self.assertEqual(48.2, target.lat)
        self.assertEqual(16.37, target.lng)

        # target with its own coordinates keeps them, ignoring the source's
        target_with_coords = Place.objects.create(
            name="Place which keeps its coordinates", lat=47.07, lng=15.44
        )
        source_other_coords = Place.objects.create(
            name="Place whose coordinates are dropped", lat=48.2, lng=16.37
        )
        target_with_coords.merge_with(source_other_coords.id)
        self.assertEqual(47.07, target_with_coords.lat)
        self.assertEqual(15.44, target_with_coords.lng)

    def test_010_delete_views(self):
        client.login(**USER)
        for x in MODELS:
            entity_type = f"{x.__name__.lower()}"
            if entity_type in ENTITY_TYPES:
                try:
                    item, _ = x.objects.get_or_create(**DUMMY_OBJECT)
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

    def test_013a_import_normdata_for_work(self):
        client.login(**USER)
        payload = {
            "normdata_url": "https://www.wikidata.org/wiki/Q105745657",
            "entity_type": "work",
        }
        url = reverse(
            "normdata:import_from_normdata",
        )
        response = client.post(url, payload, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_013b_wikidata_work_exist(self):
        entity = get_or_create_work_from_wikidata(
            "https://www.wikidata.org/wiki/Q105745657"
        )
        ic(entity)
        for x in entity.uri_set.all():
            entity = get_or_create_work_from_wikidata(x.uri)
            self.assertTrue(entity)

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

    def test_015a_dont_duplicate_first_name_in_name(self):
        """see issue https://github.com/arthur-schnitzler/pmb-service/issues/217"""
        entity = import_from_normdata(
            "https://www.wikidata.org/wiki/Q2835019", "person"
        )
        self.assertFalse(entity.first_name in entity.name)

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
        # client.login(**USER)
        # payload = {
        #     "normdata_url": "https://d-nb.info/gnd/10053010-2",
        #     "entity_type": "place",
        # }
        # url = reverse(
        #     "normdata:import_from_normdata",
        # )
        # response = client.post(url, payload, follow=True)
        # commented test because used gnd-url does not exist any longer
        self.assertEqual(200, 200)

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
        Person.objects.get_or_create(name="Andorfer", first_name="Ronja")
        Person.objects.get_or_create(name="Andorfer", first_name="Hanna")
        Place.objects.get_or_create(name="Langenlebarn")
        item = Person.objects.last()
        r = client.get(item.get_api_url())
        self.assertTrue(r.status_code, 200)
        item = Place.objects.last()
        r = client.get(item.get_api_url())
        self.assertTrue(r.status_code, 200)

    def test_022_resolver_view(self):
        Person.objects.get_or_create(name="Andorfer", first_name="Ronja")
        Person.objects.get_or_create(name="Andorfer", first_name="Hanna")
        Place.objects.get_or_create(name="Langenlebarn")
        target = Person.objects.last()
        source = Person.objects.create(name="wirdgleichgemerged")
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

    def test_024a_autocomplete_by_id(self):
        person = Person.objects.create(name="Nachnametest", first_name="Vornametest")
        url = reverse(
            "apis:apis_entities:generic_entities_autocomplete",
            kwargs={"entity": "person"},
        )
        r = client.get(f"{url}?q={person.pk}")
        self.assertEqual(r.status_code, 200)
        ids = [c["id"] for c in r.json()["results"] if "id" in c]
        self.assertIn(person.pk, ids)

    def test_024b_uri_autocomplete_by_id_shows_first_name(self):
        person = Person.objects.create(name="Nachnametest", first_name="Vornametest")
        url = reverse("apis:apis_metainfo-ac:apis_tempentity-autocomplete")
        r = client.get(f"{url}?q={person.pk}")
        self.assertEqual(r.status_code, 200)
        results = r.json()["results"]
        ids = [int(c["id"]) for c in results]
        self.assertIn(person.pk, ids)
        labels = " ".join(c["text"] for c in results)
        self.assertIn("Vornametest", labels)

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
        entity.fetch_image(override=True)
        entity.fetch_image()
        self.assertTrue(entity.img_url)

        self.assertTrue("Wikimedia Commons" in entity.img_credit_label())
        self.assertTrue("File:" in entity.img_credit())

    @mock.patch("apis_core.apis_metainfo.models.fetch_image", return_value="")
    def test_027_img_credit(self, _fetch_image):
        entity = import_from_normdata("https://www.wikidata.org/wiki/Q76483", "person")
        self.assertIsNone(entity.img_credit())
        self.assertIsNone(entity.img_credit_label())

    def test_028_beacons(self):
        grillparzer = "https://d-nb.info/gnd/118542192"
        person = Person.objects.create(name="Grillparzer")
        Uri.objects.create(domain="gnd", uri=grillparzer, entity=person)
        url = reverse("apis_core:beacon")
        r = client.get(url)
        self.assertEqual(r.status_code, 200)
        grillparzer = "https://www.wikidata.org/wiki/Q154438"
        person = Person.objects.create(name="Grillparzer")
        Uri.objects.create(domain="wikidata", uri=grillparzer, entity=person)
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

    def test_030b_order_by_written_date(self):
        # bracket content wins over the plain text; fields without brackets sort by themselves
        names = {
            "1900-02-01": Person.objects.create(
                name="a", start_date_written="1900-02-01", end_date_written="1950"
            ),
            "um 1800<1900-01-15>": Person.objects.create(
                name="b",
                start_date_written="um 1800<1900-01-15>",
                end_date_written="vor 1900<1960-05-05>",
            ),
            "1899": Person.objects.create(
                name="c", start_date_written="1899", end_date_written="1940"
            ),
            None: Person.objects.create(name="d"),
        }
        qs = Person.objects.filter(pk__in=[p.pk for p in names.values()])

        asc, _ = written_order_start_date_written(None, qs, False)
        self.assertEqual([p.name for p in asc], ["c", "b", "a", "d"])
        desc, _ = written_order_start_date_written(None, qs, True)
        self.assertEqual([p.name for p in desc], ["a", "b", "c", "d"])
        asc, _ = written_order_end_date_written(None, qs, False)
        self.assertEqual([p.name for p in asc], ["c", "a", "b", "d"])

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

    def test_032_to_iso_like(self):
        item = Person.objects.create(start_date_written="1.2.2000")
        self.assertEqual(item.start_date_written, "2000-02-01")

        item = Person.objects.create(start_date_written="2.2000")
        self.assertEqual(item.start_date_written, "2000-02")

    def test_033_date_order_validation(self):
        form_class = get_entities_form("Person")

        # end date before start date is rejected
        form = form_class(
            data={
                "name": "hansi_dates",
                "start_date_written": "1900",
                "end_date_written": "1800",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("end_date_written", form.errors)

        # end date after start date is accepted
        form = form_class(
            data={
                "name": "hansi_dates",
                "start_date_written": "1800",
                "end_date_written": "1900",
            }
        )
        self.assertTrue(form.is_valid())

        # equal start and end date is accepted
        form = form_class(
            data={
                "name": "hansi_dates",
                "start_date_written": "1900",
                "end_date_written": "1900",
            }
        )
        self.assertTrue(form.is_valid())

    def test_034_model_save_rejects_invalid_entity_date_order(self):
        with self.assertRaises(StartDateAfterEndDateError):
            Person.objects.create(
                name="hansi_invalid_dates",
                start_date_written="1900",
                end_date_written="1800",
            )

    def test_035_model_save_rejects_invalid_relation_date_order(self):
        person = Person.objects.create(name="Andorfer", first_name="Hanna")
        place = Place.objects.create(name="Langenlebarn")
        rel_type = PersonPlaceRelation.objects.create(name="geboren in")
        relation_instance = PersonPlace(
            related_person=person, related_place=place, relation_type=rel_type
        )
        relation_instance.start_date_written = "1900"
        relation_instance.end_date_written = "1800"

        with self.assertRaises(StartDateAfterEndDateError):
            relation_instance.save()


class DomainCrossingTestCase(TestCase):
    """Tests für die Schnittmengen-Ansicht (Domains kreuzen)."""

    @classmethod
    def setUpTestData(cls):
        # Jede angelegte Entität erhält automatisch eine "pmb"-URI.
        cls.p_both = Person.objects.create(
            name="Both", first_name="Anna", gender="female"
        )
        cls.p_gnd = Person.objects.create(name="GndOnly", gender="male")
        cls.p_wiki = Person.objects.create(name="WikiOnly", gender="third gender")
        cls.place_gnd = Place.objects.create(name="PlaceGnd")

        Uri.objects.create(
            uri="https://d-nb.info/gnd/both", domain="gnd", entity=cls.p_both
        )
        Uri.objects.create(
            uri="https://www.wikidata.org/entity/both",
            domain="wikidata",
            entity=cls.p_both,
        )
        Uri.objects.create(
            uri="https://d-nb.info/gnd/gndonly", domain="gnd", entity=cls.p_gnd
        )
        Uri.objects.create(
            uri="https://www.wikidata.org/entity/wikionly",
            domain="wikidata",
            entity=cls.p_wiki,
        )
        Uri.objects.create(
            uri="https://d-nb.info/gnd/place", domain="gnd", entity=cls.place_gnd
        )

    def setUp(self):
        User.objects.create_user(**USER)
        self.client = Client()
        self.client.login(**USER)
        self.url = reverse("apis:apis_entities:domain_crossing")

    def _names(self, response):
        return {row.record.name for row in response.context["table"].rows}

    def test_intersection(self):
        response = self.client.get(
            f"{self.url}?type=person&mode=intersection&d=gnd&d=wikidata"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._names(response), {"Both"})

    def test_union(self):
        response = self.client.get(
            f"{self.url}?type=person&mode=union&d=gnd&d=wikidata"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._names(response), {"Both", "GndOnly", "WikiOnly"})

    def test_difference(self):
        response = self.client.get(
            f"{self.url}?type=person&mode=difference&base=gnd&d=wikidata"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._names(response), {"GndOnly"})

    def test_entity_type_switch(self):
        response = self.client.get(f"{self.url}?type=place&mode=intersection&d=gnd")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._names(response), {"PlaceGnd"})

    def test_no_domain_selected_returns_empty(self):
        response = self.client.get(f"{self.url}?type=person&mode=intersection")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total"], 0)

    def test_invalid_type_falls_back_to_person(self):
        response = self.client.get(f"{self.url}?type=nonsense&mode=union&d=gnd")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["entity"], "person")
        self.assertEqual(self._names(response), {"Both", "GndOnly"})

    def test_gender_female(self):
        response = self.client.get(
            f"{self.url}?type=person&mode=union&d=gnd&d=wikidata&gender=female"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._names(response), {"Both"})

    def test_gender_male(self):
        response = self.client.get(
            f"{self.url}?type=person&mode=union&d=gnd&d=wikidata&gender=male"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._names(response), {"GndOnly"})

    def test_gender_other(self):
        # "anderes oder nicht ausgezeichnet" umfasst u.a. "third gender"
        response = self.client.get(
            f"{self.url}?type=person&mode=union&d=gnd&d=wikidata&gender=other"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._names(response), {"WikiOnly"})

    def test_gender_ignored_for_non_person(self):
        response = self.client.get(
            f"{self.url}?type=place&mode=intersection&d=gnd&gender=female"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._names(response), {"PlaceGnd"})
        self.assertEqual(response.context["gender_buttons"], [])

    def test_first_name_column_for_person(self):
        response = self.client.get(f"{self.url}?type=person&mode=union&d=gnd")
        self.assertEqual(response.status_code, 200)
        self.assertIn("first_name", response.context["table"].columns.names())

    def test_union_without_domains_is_empty(self):
        response = self.client.get(f"{self.url}?type=person&mode=union")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total"], 0)

    def test_difference_without_base_is_empty(self):
        response = self.client.get(f"{self.url}?type=person&mode=difference&d=gnd")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total"], 0)

    def test_difference_base_only_without_exclusion(self):
        response = self.client.get(f"{self.url}?type=person&mode=difference&base=gnd")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._names(response), {"Both", "GndOnly"})

    def test_invalid_gender_is_ignored(self):
        response = self.client.get(
            f"{self.url}?type=person&mode=union&d=gnd&gender=nonsense"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["gender"])
        self.assertEqual(self._names(response), {"Both", "GndOnly"})

    def test_default_page_without_params(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["entity"], "person")
        self.assertEqual(response.context["mode"], "intersection")
        self.assertEqual(response.context["total"], 0)

    def test_invalid_mode_falls_back_to_intersection(self):
        response = self.client.get(
            f"{self.url}?type=person&mode=nonsense&d=gnd&d=wikidata"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["mode"], "intersection")
        self.assertEqual(self._names(response), {"Both"})

    def test_mode_tooltips_rendered(self):
        response = self.client.get(f"{self.url}?type=person&mode=intersection&d=gnd")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-bs-toggle="tooltip"')
        self.assertContains(response, "in allen gewählten Domains vorkommen")

    def test_export_csv(self):
        response = self.client.get(
            f"{self.url}?type=person&mode=union&d=gnd&d=wikidata&_export=csv"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertIn("schnittmengen.csv", response["Content-Disposition"])
        content = response.getvalue().decode("utf-8")
        self.assertIn("Both", content)
        self.assertNotIn("<a", content)

    def test_export_json(self):
        response = self.client.get(
            f"{self.url}?type=person&mode=union&d=gnd&d=wikidata&_export=json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("schnittmengen.json", response["Content-Disposition"])
        self.assertIn("Both", response.getvalue().decode("utf-8"))

    def test_invalid_export_format_renders_page(self):
        response = self.client.get(
            f"{self.url}?type=person&mode=union&d=gnd&_export=nonsense"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "apis_entities/domain_crossing.html")


class RelationSectionHeaderTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = Person.objects.create(name="Bahr", first_name="Hermann")
        cls.place = Place.objects.create(name="Linz")
        cls.rel_type = PersonPlaceRelation.objects.create(name="wohnt in")

    def _create_relations(self, years):
        for year in years:
            PersonPlace.objects.create(
                related_person=self.person,
                related_place=self.place,
                relation_type=self.rel_type,
                start_date_written=year,
            )

    def _get_detail_page(self, person=None):
        return self.client.get((person or self.person).get_absolute_url())

    def _get_section(self, response, title):
        return next(x for x in response.context["right_card"] if x[0] == title)

    def test_more_relations_than_limit_show_count_and_button(self):
        self._create_relations(str(year) for year in range(1900, 1913))

        response = self._get_detail_page()

        list_url = f"{PersonPlace.get_listview_url()}?source_target={self.person.pk}"
        self.assertContains(response, "10 von 13")
        self.assertContains(response, "Alle 13 Beziehungen anzeigen")
        self.assertContains(response, f'href="{list_url}"')
        self.assertContains(response, "--relation-action: var(--person)")
        self.assertContains(response, "relation-section-header__button")
        self.assertNotContains(response, "relation-section-header__link")
        self.assertNotContains(response, "maximal 10 Beziehungen")

    def test_relations_within_limit_show_link_without_frame(self):
        self._create_relations(str(year) for year in range(1900, 1910))

        response = self._get_detail_page()

        self.assertContains(response, "Alle 10 Beziehungen anzeigen")
        self.assertContains(response, "relation-section-header__link")
        self.assertNotContains(response, "relation-section-header__button")
        self.assertNotContains(response, "10 von 10")

    def test_single_relation_uses_singular(self):
        self._create_relations(["1900"])

        response = self._get_detail_page()

        self.assertContains(response, "1 Beziehung anzeigen")
        self.assertNotContains(response, "Alle 1 Beziehung")

    def test_preview_lists_chronologically_first_relations(self):
        self._create_relations(["", *(str(year) for year in range(1911, 1899, -1))])

        response = self._get_detail_page()

        rows = self._get_section(response, "Place")[1].rows
        self.assertEqual(
            [row.record.start_date.year for row in rows],
            list(range(1900, 1910)),
        )

    def test_self_relation_counts_both_directions(self):
        other = Person.objects.create(name="Schnitzler", first_name="Arthur")
        rel_type = PersonPersonRelation.objects.create(name="kennt")
        for index in range(11):
            first, second = (self.person, other) if index % 2 else (other, self.person)
            PersonPerson.objects.create(
                related_persona=first, related_personb=second, relation_type=rel_type
            )

        response = self._get_detail_page()

        self.assertContains(response, "10 von 11")
        self.assertContains(response, "Alle 11 Beziehungen anzeigen")

    def test_label_section_has_neither_count_nor_link(self):
        label_type = LabelType.objects.create(name="Pseudonym")
        Label.objects.create(
            label="Mörder", label_type=label_type, temp_entity=self.person
        )

        response = self._get_detail_page()

        self.assertContains(response, "<h4>Label</h4>")
        self.assertNotContains(response, "relation-section-header__link")
        self.assertNotContains(response, "Beziehungen anzeigen")

    def _get_edit_page(self, params=""):
        self.client.force_login(User.objects.create_user(**USER))
        url = reverse(
            "apis:apis_entities:generic_entities_edit_view",
            kwargs={"pk": self.person.pk, "entity": "person"},
        )
        return self.client.get(f"{url}{params}")

    def test_edit_view_shows_newest_relations_first(self):
        years = [1905, 1900, 1912, 1903, 1908, 1901, 1911, 1904, 1909, 1902, 1910, 1906]
        self._create_relations(str(year) for year in years)

        response = self._get_edit_page()

        rows = self._get_section(response, "Place")[1].rows
        self.assertEqual(
            [row.record.start_date.year for row in rows],
            years[:1:-1],
        )
        self.assertContains(response, "10 von 12")
        self.assertContains(response, "Alle 12 Beziehungen anzeigen")
        self.assertContains(response, "relation-section-header__button")
        self.assertNotContains(response, "maximal 10 Beziehungen")

    def test_table_after_saving_lists_new_relation_first(self):
        self._create_relations(["1901", "1902"])
        self.client.force_login(User.objects.create_user(**USER))

        response = self.client.post(
            f"/apis/relations/ajax/save/person/PersonPlaceForm/{self.person.pk}/",
            {
                "relation_type": self.rel_type.pk,
                "target": self.place.pk,
                "start_date_written": "1950",
            },
        )

        content = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertLess(content.index("1950"), content.index("1902"))
        self.assertLess(content.index("1902"), content.index("1901"))

    def test_edit_view_section_within_limit_shows_link_without_frame(self):
        self._create_relations(str(year) for year in range(1900, 1910))

        response = self._get_edit_page()

        self.assertContains(response, "Alle 10 Beziehungen anzeigen")
        self.assertContains(response, "relation-section-header__link")
        self.assertNotContains(response, "relation-section-header__button")
        self.assertNotContains(response, "10 von 10")

    def test_edit_view_empty_section_keeps_heading_without_link(self):
        response = self._get_edit_page()

        self.assertContains(response, "<h4>Place</h4>")
        self.assertNotContains(response, "relation-section-header__link")
        self.assertNotContains(response, "Beziehungen anzeigen")

    def test_edit_view_ignores_sort_parameter(self):
        self._create_relations(str(year) for year in range(1900, 1913))

        response = self._get_edit_page("?PePl-sort=start_date_written")

        self.assertEqual(response.status_code, 200)
        rows = self._get_section(response, "Place")[1].rows
        self.assertEqual(rows[0].record.start_date.year, 1912)


class EntityColorsTestCase(SimpleTestCase):
    ENTITY_MODELS = {
        "person": Person,
        "place": Place,
        "work": Work,
        "event": Event,
        "institution": Institution,
    }

    def _read_static_file(self, path):
        return (settings.BASE_DIR / path).read_text(encoding="utf-8").lower()

    def test_relation_colors_match_their_source_entity(self):
        for relation in AbstractRelation.get_all_relation_classes():
            with self.subTest(relation=relation.__name__):
                self.assertEqual(
                    relation.get_color(),
                    relation.get_related_entity_classa().get_color(),
                )

    def test_entity_colors_match_css_and_network_graph(self):
        css = self._read_static_file("static/css/style.css")
        network_js = self._read_static_file("static/src/js/lib.js")
        for name, model in self.ENTITY_MODELS.items():
            with self.subTest(entity=name):
                self.assertIn(f"--{name}: {model.get_color()};", css)
                self.assertIn(f'{name}: "{model.get_color()}"', network_js)


class MostValuableEntityViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = Person.objects.create(name="Frequently Referenced Person")
        cls.place = Place.objects.create(name="Frequently Referenced Place")

        for index in range(14):
            domain = f"source-{index}"
            Uri.objects.create(
                uri=f"https://{domain}.example.org/person/{index}",
                domain=domain,
                entity=cls.person,
            )
            Uri.objects.create(
                uri=f"https://{domain}.example.org/place/{index}",
                domain=domain,
                entity=cls.place,
            )

        Uri.objects.create(
            uri="https://source-0.example.org/person/duplicate",
            domain="source-0",
            entity=cls.person,
        )

    def setUp(self):
        User.objects.create_user(**USER)
        self.client = Client()
        self.client.login(**USER)

    def test_reports_persons_only_and_deduplicates_external_uris(self):
        url = reverse("apis:apis_entities:mvp")
        response = self.client.get(f"{url}?type=person")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["entity"], "person")
        self.assertEqual(response.context["uri_count"], 1)
        self.assertEqual(len(response.context["rows"]), 1)

        row = response.context["rows"][0]
        self.assertEqual(row["entity"], self.person.pk)
        self.assertEqual(row["entity__name"], self.person.name)
        self.assertEqual(row["count"], 15)
        self.assertEqual(len(row["uris"]), 15)

    def test_export_csv(self):
        url = reverse("apis:apis_entities:mvp")
        response = self.client.get(f"{url}?type=person&_export=csv")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("attachment;", response["Content-Disposition"])
        content = response.content.decode()
        self.assertIn(self.person.name, content)
        self.assertIn("15", content)

    def test_export_json(self):
        url = reverse("apis:apis_entities:mvp")
        response = self.client.get(f"{url}?type=person&_export=json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertIn("attachment;", response["Content-Disposition"])
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.person.pk)
        self.assertEqual(data[0]["name"], self.person.name)
        self.assertEqual(data[0]["count"], 15)
