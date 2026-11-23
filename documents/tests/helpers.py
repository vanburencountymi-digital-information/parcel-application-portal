import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from documents.types import DocumentType

PDF_BYTES = b"%PDF-1.7\n%test file\n"
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 16
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16

# Folder that `DocumentFactory` stores files under by default.
TEST_FOLDER = "applications/test"

# One temp folder for the whole test run, so tests never write into the real MEDIA_ROOT.
# Deleted when the test process exits.
_TEMP_DIR = tempfile.TemporaryDirectory()
TEMP_MEDIA = _TEMP_DIR.name

# Put on any test class that saves a `Document`: files go to local temp storage.
use_temp_storage = override_settings(
    MEDIA_ROOT=TEMP_MEDIA,
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
)


def make_upload(
    name: str = "deed.pdf",
    content: bytes = PDF_BYTES,
    content_type: str = DocumentType.PDF.value,
) -> SimpleUploadedFile:
    """An in-memory upload. Defaults to a tiny valid PDF.

    Takes: the file name, its bytes, and the MIME type the upload claims.
    Returns: a `SimpleUploadedFile`.
    """
    return SimpleUploadedFile(name, content, content_type=content_type)
