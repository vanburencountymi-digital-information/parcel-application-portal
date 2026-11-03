from django.core.files.uploadedfile import SimpleUploadedFile

from documents.models import Document
from documents.services import DocumentService

PDF_BYTES = b"%PDF-1.7\n%test file\n"
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 16
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


def make_upload(
    name: str = "deed.pdf",
    content: bytes = PDF_BYTES,
    content_type: str = "application/pdf",
) -> SimpleUploadedFile:
    """An in-memory upload. Defaults to a tiny valid PDF."""
    return SimpleUploadedFile(name, content, content_type=content_type)


def make_document(folder: str = "applications/test", **upload_kwargs: str | bytes) -> Document:
    """A saved `Document`, created the same way real uploads are."""
    return DocumentService().upload(make_upload(**upload_kwargs), folder=folder)  # type: ignore[arg-type]
