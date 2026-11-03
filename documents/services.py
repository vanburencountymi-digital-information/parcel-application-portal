import hashlib

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import UploadedFile
from django.template.defaultfilters import filesizeformat
from django.utils.text import get_text_list

from documents.adapters import FileTypeAdapter
from documents.exceptions import DocumentValidationError
from documents.models import Document
from documents.types import DocumentType


class DocumentService:
    """Accepts uploaded files: checks them, stores them, and records them as `Document`s.

    The file type is worked out by a `FileTypeAdapter`, which tests can replace.
    """

    def __init__(self, file_type_adapter: FileTypeAdapter | None = None) -> None:
        self._file_type_adapter = file_type_adapter or FileTypeAdapter()

    def upload(
        self,
        uploaded_file: UploadedFile,
        *,
        folder: str,
        uploader: User | None = None,
    ) -> Document:
        """Checks an uploaded file, stores it and records it.

        Takes: the upload, the folder to store it in (for example
        "applications/<application id>"), and who uploaded it.
        Returns: the saved `Document`.
        Raises: `DocumentValidationError` if the file or folder is not acceptable.
        Nothing is stored in that case.
        """
        folder = self._validated_folder(folder)
        size = self._validated_size(uploaded_file)
        document_type = self._detect_type(uploaded_file)

        document = Document(
            # Keep the end of a long name, not the start, so the extension survives.
            original_name=(uploaded_file.name or "")[-255:],
            content_type=document_type.value,
            size=size,
            sha256=self._hash(uploaded_file),
            uploader=uploader,
        )
        # The stored name is built here from the document's id, never from the
        # uploader's filename.
        document.file.save(
            f"{folder}/{document.id}.{document_type.extension}", uploaded_file, save=False
        )
        try:
            document.save()
        except Exception:
            # Don't leave a file behind that no row points to.
            document.file.delete(save=False)
            raise
        return document

    def _validated_folder(self, folder: str) -> str:
        """Checks the folder is a safe relative path.

        Takes: the folder the caller asked for.
        Returns: the folder with surrounding spaces and slashes removed.
        Raises: `DocumentValidationError` if it is empty or could escape its folder.
        """
        cleaned = folder.strip().strip("/")
        parts = cleaned.split("/")
        # Guards against path traversal: no "..", no leading "/" or backslashes, and no
        # empty parts (a doubled "//").
        if not cleaned or "\\" in folder or folder.startswith("/") or ".." in parts or "" in parts:
            raise DocumentValidationError("Invalid upload folder.")
        return cleaned

    def _validated_size(self, uploaded_file: UploadedFile) -> int:
        """Checks the file is not empty and not over the size limit.

        Takes: the upload.
        Returns: its size in bytes.
        Raises: `DocumentValidationError` if it is empty or too large.
        """
        # Django can report a size of None for some uploads; treat that as empty.
        size = uploaded_file.size or 0
        limit = settings.DOCUMENT_MAX_UPLOAD_BYTES
        if size == 0:
            raise DocumentValidationError("The file is empty.")
        if size > limit:
            raise DocumentValidationError(
                f"The file is too large. The limit is {filesizeformat(limit)}."
            )
        return size

    def _detect_type(self, uploaded_file: UploadedFile) -> DocumentType:
        """Works out the file's type from its first bytes.

        Takes: the upload.
        Returns: its `DocumentType`.
        Raises: `DocumentValidationError` if it is not a type we accept.
        """
        uploaded_file.seek(0)
        header = uploaded_file.read(settings.DOCUMENT_HEADER_BYTES)
        # Rewind: the file is read again to hash and to store it.
        uploaded_file.seek(0)
        # The adapter looks at the file's first bytes (its signature) instead of trusting
        # the extension or the browser's claimed type, both of which the uploader controls.
        mime = self._file_type_adapter.detect(header)
        if mime in DocumentType.values:
            return DocumentType(mime)
        accepted = get_text_list(DocumentType.labels, "and")
        raise DocumentValidationError(f"Only {accepted} files are accepted.")

    def _hash(self, uploaded_file: UploadedFile) -> str:
        """Takes: the upload. Returns: its SHA-256 hash as hex text."""
        hasher = hashlib.sha256()
        for chunk in uploaded_file.chunks():
            hasher.update(chunk)
        # Rewind: the file is read again to store it.
        uploaded_file.seek(0)
        return hasher.hexdigest()
