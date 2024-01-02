import os

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from apis_core.apis_entities.models import Person
from apis_core.apis_metainfo.models import Uri
from normdata.utils import import_from_normdata

client = Client()
USER = {"username": "testuser", "password": "password", "is_active": True}
BAHR = {"name": "Bahr", "first_name": "Hermann", "start_date_written": "1900"}

ENTITY_TYPES = ["person", "place", "event", "work", "institution"]

MODELS = list(apps.all_models["apis_entities"].values())
MEDIA_ROOT = settings.MEDIA_ROOT

URIS = [
    ("https://www.geonames.org/2772400/linz.html", "place"),
    ("https://www.wikidata.org/wiki/Q100965214", "person"),
    ("https://d-nb.info/gnd/118609807", "person"),
    ("https://d-nb.info/gnd/118757393", "person"),
]


class DumperTestCase(TestCase):
    def setUp(self):
        User.objects.create_user(**USER)
        Person.objects.create(**BAHR)
        for x in URIS:
            import_from_normdata(x[0], x[1])

    def test_01_dump_data(self):
        call_command("dump_entities", "--limit")
        with open(os.path.join(MEDIA_ROOT, "listperson.xml"), "r") as f:
            data = f.read()
        self.assertTrue("Schnitzler" in data)

    def test_02_wikipedia_minter(self):
        call_command("wikipedia_minter")
        uris = Uri.objects.filter(domain="wikipedia")
        self.assertTrue(uris.count())

    def test_03_beacon(self):
        domain = "thun-korrespondenz"
        call_command(
            "process_beacon",
            beacon="https://thun-korrespondenz.acdh.oeaw.ac.at/beacon.txt",
            domain=domain,
        )
        uris = Uri.objects.filter(domain=domain)
        self.assertTrue(uris.count())

    def test_04_wikidata_minter(self):
        Uri.objects.filter(domain="wikidata").first().delete()
        before_uris = Uri.objects.all().count()
        call_command("wikidata_minter")
        after_uris = Uri.objects.all().count()
        self.assertTrue(before_uris < after_uris)

    def test_05_startpage(self):
        url = reverse("dumper:home")
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_06_login_and_out(self):
        rv = self.client.get(reverse("dumper:home"))
        self.assertEqual(rv.status_code, 200)
        self.assertContains(rv, "Personen der Moderne Basis")
        rv = self.client.get(reverse("dumper:user_login"))
        self.assertContains(rv, "Username")
        form_data = {"username": "temporary", "password": "temporary"}
        rv = self.client.post(reverse("dumper:user_login"), form_data, follow=True)
        rv = self.client.get(reverse("dumper:user_logout"), follow=True)
        self.assertContains(rv, "Küss die Hand")
        form_data = {"username": "whatever", "password": USER["password"]}
        rv = self.client.post(reverse("dumper:user_login"), form_data, follow=True)
        self.assertContains(rv, "user does not exist")
