from django.test import TestCase

from documents.models import Document
from documents.tests.factories import DocumentFactory
from documents.tests.helpers import use_temp_storage
from documents.types import DocumentType


@use_temp_storage
class DocumentTests(TestCase):
    def test_factory_saves_a_valid_document(self) -> None:
        document = DocumentFactory.create(original_name="survey.pdf")

        self.assertTrue(Document.objects.filter(pk=document.pk).exists())
        self.assertEqual(document.content_type, DocumentType.PDF.value)

    def test_factory_stores_under_the_given_folder(self) -> None:
        document = DocumentFactory.create(folder="applications/7")

        self.assertIn("applications/7/", str(document.file.name))

    def test_str_is_the_original_name(self) -> None:
        self.assertEqual(str(DocumentFactory.create(original_name="survey.pdf")), "survey.pdf")
