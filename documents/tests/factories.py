from typing import Any

from factory import LazyAttribute
from factory.django import DjangoModelFactory

from documents.models import Document
from documents.services import DocumentService
from documents.tests.helpers import TEST_FOLDER, make_upload


class DocumentFactory(DjangoModelFactory[Document]):
    """A saved `Document`, created through `DocumentService` the same way real uploads are.

    Takes: `original_name` (the upload's file name), `file` (the upload itself, a valid PDF
    by default), `uploader`, and `folder` (where it is stored).
    Returns: the saved `Document`. Its stored name and type come from the service, which
    reads them from `file`, so pass `file` to change them.
    To test other file types, call `DocumentService.upload` directly with `make_upload`.
    """

    class Meta:
        model = Document

    original_name = "deed.pdf"
    uploader = None
    folder = TEST_FOLDER
    file = LazyAttribute(lambda o: make_upload(o.original_name))

    @classmethod
    def _create(cls, model_class: type[Document], *args: Any, **kwargs: Any) -> Document:
        # Goes through the service, not Document.objects.create, so the checks and storage match real uploads.
        return DocumentService().upload(
            kwargs.pop("file"), folder=kwargs.pop("folder"), uploader=kwargs.pop("uploader")
        )
