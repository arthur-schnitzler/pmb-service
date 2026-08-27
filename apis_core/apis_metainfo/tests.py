# Create your tests here.

from django.apps import apps
from django.contrib.auth.models import User
from django.test import Client, TestCase

from apis_core.apis_entities.models import Person
from apis_core.apis_metainfo.models import Collection, Uri

client = Client()
USER = {"username": "testuser", "password": "somepassword"}
BAHR = {"name": "Bahr", "first_name": "Hermann", "start_date_written": "1900"}
DUMMY_OBJECT = {"name": "test", "start_date_written": "1900"}

ENTITY_TYPES = ["person", "place", "event", "work", "institution"]

MODELS = list(apps.all_models["apis_entities"].values())

RELATION_MODELS = list(apps.all_models["apis_relations"].values())
DOMAIN = "hansi4ever"


class EntitiesTestCase(TestCase):
    def setUp(self):
        User.objects.create_user(**USER)

    def test_001_collection_domain_entities(self):
        ronja = Person.objects.create(name="Ronja")
        hanna = Person.objects.create(name="Hanna")
        Uri.objects.create(uri="https://foo/bar/roo/1", domain=DOMAIN, entity=ronja)
        Uri.objects.create(uri="https://foo/bar/roo/2", domain=DOMAIN, entity=ronja)
        col = Collection.objects.create(name="foo", related_domain=[DOMAIN])
        new_col = Collection.objects.create(
            name="foobar", related_domain=[DOMAIN, "karl"]
        )
        Uri.objects.create(uri="https://foo/bar/roo/3", domain="karl", entity=hanna)
        rel_ents = col.get_related_entities_count()
        print(f"#########################{rel_ents}")
        self.assertEqual(rel_ents, 1)
        rel_uris = col.get_related_uris().count()
        self.assertEqual(rel_uris, 2)

        rel_ents = new_col.get_related_entities_count()
        self.assertEqual(rel_ents, 2)
        print(f"#########################{rel_ents}")
        rel_uris = new_col.get_related_uris().count()
        self.assertEqual(rel_uris, 3)
