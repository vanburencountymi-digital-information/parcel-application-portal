from django.test import SimpleTestCase
from parameterized import parameterized

from documents.adapters import FileTypeAdapter
from documents.tests.factories import JPEG_BYTES, PDF_BYTES, PNG_BYTES


class FileTypeAdapterTests(SimpleTestCase):
    @parameterized.expand(
        [
            ("pdf", PDF_BYTES, "application/pdf"),
            ("jpeg", JPEG_BYTES, "image/jpeg"),
            ("png", PNG_BYTES, "image/png"),
            ("text", b"just some text", None),
            ("empty", b"", None),
        ]
    )
    def test_detect(self, _name: str, header: bytes, expected: str | None) -> None:
        self.assertEqual(FileTypeAdapter().detect(header), expected)
