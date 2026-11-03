from django.db import models


class DocumentType(models.TextChoices):
    """The file types `DocumentService` accepts. The value is the MIME type that
    `filetype` reports and that we store on `Document.content_type`.

    To accept another type, add it here and to `_EXTENSIONS`.
    """

    PDF = "application/pdf", "PDF"
    JPEG = "image/jpeg", "JPG"
    PNG = "image/png", "PNG"

    @property
    def extension(self) -> str:
        """Takes: nothing. Returns: the extension we store this type under, without the dot."""
        return _EXTENSIONS[self]


_EXTENSIONS = {
    DocumentType.PDF: "pdf",
    DocumentType.JPEG: "jpg",
    DocumentType.PNG: "png",
}
