from uuid import uuid4

from django.conf import settings
from django.db import models


class Document(models.Model):
    """A file someone uploaded. Knows nothing about applications; other apps link to it.

    Create these through `DocumentService`, which checks the file, fills in the name,
    type, size and hash, and chooses the storage path (a caller-supplied folder plus the
    document's id, never the uploader's filename).
    """

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    file = models.FileField(upload_to="", max_length=255)
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.PositiveBigIntegerField(help_text="Size in bytes.")
    # Recorded so duplicates can be spotted later. Not unique on purpose.
    sha256 = models.CharField(max_length=64, db_index=True)
    # SET_NULL so deleting an account never deletes the evidence it uploaded.
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.original_name
