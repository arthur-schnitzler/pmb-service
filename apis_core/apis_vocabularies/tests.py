from django.core.exceptions import ValidationError
from django.test import TestCase

from apis_core.apis_vocabularies.models import ProfessionType


class ProfessionTypeTests(TestCase):
    def test_cannot_create_duplicate_profession_type_name(self):
        ProfessionType.objects.create(name="Editor")

        with self.assertRaises(ValidationError):
            ProfessionType.objects.create(name="Editor")

    def test_can_update_existing_profession_type_without_false_duplicate(self):
        profession = ProfessionType.objects.create(name="Translator")
        profession.description = "Updated"
        profession.save()

        self.assertEqual(ProfessionType.objects.count(), 1)

    def test_normalized_duplicate_name_is_rejected(self):
        ProfessionType.objects.create(name="Café")

        decomposed = "Cafe\u0301"
        with self.assertRaises(ValidationError):
            ProfessionType.objects.create(name=decomposed)
