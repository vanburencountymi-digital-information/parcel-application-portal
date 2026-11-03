from django.test import SimpleTestCase
from parameterized import parameterized

from documents.types import DocumentType


class DocumentTypeTests(SimpleTestCase):
    @parameterized.expand(
        [
            (DocumentType.PDF, "application/pdf", "pdf"),
            (DocumentType.JPEG, "image/jpeg", "jpg"),
            (DocumentType.PNG, "image/png", "png"),
        ]
    )
    def test_value_and_extension(
        self, document_type: DocumentType, mime: str, extension: str
    ) -> None:
        self.assertEqual(document_type.value, mime)
        self.assertEqual(document_type.extension, extension)

    def test_every_type_has_an_extension(self) -> None:
        for document_type in DocumentType:
            self.assertTrue(document_type.extension)
