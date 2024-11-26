from django.apps import apps
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from dumper.utils import gsheet_to_df, process_beacon
from normdata.utils import import_from_normdata


client = Client()
USER = {"username": "testuser", "password": "password", "is_active": True}
BAHR = {"name": "Schnitzler", "first_name": "Hermann", "start_date_written": "1900"}

ENTITY_TYPES = ["person", "place", "event", "work", "institution"]

MODELS = list(apps.all_models["apis_entities"].values())
MEDIA_ROOT = settings.MEDIA_ROOT


TEST_CSV = "hansi.csv"


class DumperTestCase(TestCase):
    fixtures = [
        "db.json",
    ]

    def test_01_dl_gsheet(self):
        sheet_id = "1QVb62GiWx9MdEGUNTKaFsZ10rfV-s-PJW3QmVKG2EUQ"
        df = gsheet_to_df(sheet_id)
        df.to_csv(TEST_CSV, index=False)
        self.assertTrue("foo" in list(df.keys()))

    def test_03_beacon(self):
        import_from_normdata("https://d-nb.info/gnd/118757393", "person")
        domain = "thun-korrespondenz"
        processed = process_beacon(
            "https://thun-korrespondenz.acdh.oeaw.ac.at/beacon.txt", domain=domain
        )
        self.assertTrue(processed > 0)

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

    def test_07_imprint(self):
        url = reverse("dumper:imprint")
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_08_imprint(self):
        url = reverse("dumper:about")
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_09_imprint(self):
        url = reverse("dumper:export")
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
