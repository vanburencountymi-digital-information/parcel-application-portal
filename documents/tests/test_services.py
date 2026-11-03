import hashlib
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, create_autospec, patch

from django.contrib.auth.models import User
from django.template.defaultfilters import filesizeformat
from django.test import TestCase, override_settings
from parameterized import parameterized

from documents.adapters import FileTypeAdapter
from documents.exceptions import DocumentValidationError
from documents.models import Document
from documents.services import DocumentService
from documents.tests.factories import JPEG_BYTES, PDF_BYTES, PNG_BYTES, make_upload

_TEMP_MEDIA = tempfile.mkdtemp()


@override_settings(
    MEDIA_ROOT=_TEMP_MEDIA,
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
)
class DocumentServiceUploadTests(TestCase):
    user: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user("uploader", password="x")  # noqa: S106

    def setUp(self) -> None:
        self.service = DocumentService()

    @parameterized.expand(
        [
            ("pdf", "deed.pdf", PDF_BYTES, "application/pdf"),
            ("jpg", "photo.jpg", JPEG_BYTES, "image/jpeg"),
            ("png", "scan.png", PNG_BYTES, "image/png"),
        ]
    )
    def test_upload_records_the_file(
        self, extension: str, name: str, content: bytes, content_type: str
    ) -> None:
        document = self.service.upload(
            make_upload(name, content), folder="applications/42", uploader=self.user
        )

        self.assertEqual(document.original_name, name)
        self.assertEqual(document.content_type, content_type)
        self.assertEqual(document.size, len(content))
        self.assertEqual(document.sha256, hashlib.sha256(content).hexdigest())
        self.assertEqual(document.uploader, self.user)
        self.assertEqual(document.file.name, f"applications/42/{document.id}.{extension}")
        self.assertEqual(Path(document.file.path).read_bytes(), content)

    def test_type_comes_from_contents_not_name_or_claimed_type(self) -> None:
        upload = make_upload("scan.png", PDF_BYTES, content_type="image/png")

        document = self.service.upload(upload, folder="applications/1")

        self.assertEqual(document.content_type, "application/pdf")
        self.assertTrue(str(document.file.name).endswith(".pdf"))

    def test_stored_name_ignores_the_uploaders_filename(self) -> None:
        document = self.service.upload(make_upload("../../evil.pdf"), folder="applications/1")

        self.assertEqual(document.file.name, f"applications/1/{document.id}.pdf")

    def test_uploader_is_optional(self) -> None:
        document = self.service.upload(make_upload(), folder="applications/1")

        self.assertIsNone(document.uploader)

    @parameterized.expand(
        [
            ("not_allowed_type", b"just some text", "Only PDF, JPG and PNG"),
            ("empty", b"", "empty"),
        ]
    )
    def test_refused_files_store_nothing(self, _name: str, content: bytes, message: str) -> None:
        with self.assertRaisesMessage(DocumentValidationError, message):
            self.service.upload(make_upload("file.pdf", content), folder="applications/1")

        self.assertEqual(Document.objects.count(), 0)

    @override_settings(DOCUMENT_MAX_UPLOAD_BYTES=1024 * 1024)
    def test_files_over_the_configured_limit_are_refused(self) -> None:
        too_big = PDF_BYTES + b"0" * (1024 * 1024)

        with self.assertRaisesMessage(
            DocumentValidationError, f"The limit is {filesizeformat(1024 * 1024)}"
        ):
            self.service.upload(make_upload("big.pdf", too_big), folder="applications/1")

        self.assertEqual(Document.objects.count(), 0)

    @override_settings(DOCUMENT_MAX_UPLOAD_BYTES=1024 * 1024)
    def test_a_file_at_the_limit_is_accepted(self) -> None:
        at_limit = PDF_BYTES + b"0" * (1024 * 1024 - len(PDF_BYTES))

        document = self.service.upload(make_upload("ok.pdf", at_limit), folder="applications/1")

        self.assertEqual(document.size, 1024 * 1024)

    @parameterized.expand(
        [
            ("recognized", "application/pdf", None),
            ("unknown_to_adapter", None, "Only PDF"),
            ("recognized_but_not_allowed", "application/zip", "Only PDF"),
        ]
    )
    def test_type_comes_from_the_injected_adapter(
        self, _name: str, detected: str | None, error: str | None
    ) -> None:
        adapter = create_autospec(FileTypeAdapter, instance=True)
        adapter.detect.return_value = detected
        service = DocumentService(file_type_adapter=adapter)
        # Contents that are not a PDF, to show the adapter's answer is what counts.
        upload = make_upload("odd.bin", b"not really a pdf")

        if error:
            with self.assertRaisesMessage(DocumentValidationError, error):
                service.upload(upload, folder="applications/1")
        else:
            document = service.upload(upload, folder="applications/1")
            self.assertEqual(document.content_type, "application/pdf")
        adapter.detect.assert_called_once()

    @override_settings(DOCUMENT_HEADER_BYTES=2)
    def test_header_size_setting_limits_how_much_is_read_to_detect_the_type(self) -> None:
        # Two bytes is too little to recognize a PDF, so it is refused.
        with self.assertRaisesMessage(DocumentValidationError, "Only PDF"):
            self.service.upload(make_upload(), folder="applications/1")

    @parameterized.expand(
        [
            ("empty", ""),
            ("blank", "  "),
            ("absolute", "/applications/1"),
            ("parent", "applications/../other"),
            ("backslash", "applications\\1"),
            ("double_slash", "applications//1"),
        ]
    )
    def test_bad_folders_are_refused(self, _name: str, folder: str) -> None:
        with self.assertRaisesMessage(DocumentValidationError, "folder"):
            self.service.upload(make_upload(), folder=folder)

        self.assertEqual(Document.objects.count(), 0)

    @patch.object(Document, "save", autospec=True, side_effect=RuntimeError("db down"))
    def test_file_is_removed_if_the_row_cannot_be_saved(self, _save: MagicMock) -> None:
        stored_before = list(Path(_TEMP_MEDIA).rglob("*.pdf"))

        with self.assertRaises(RuntimeError):
            self.service.upload(make_upload(), folder="applications/rollback")

        self.assertEqual(list(Path(_TEMP_MEDIA).rglob("*.pdf")), stored_before)
