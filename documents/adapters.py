import filetype


class FileTypeAdapter:
    """Works out a file's type from its first bytes. The only place that imports
    `filetype`, so switching to another library later means changing just this class.
    """

    def detect(self, header: bytes) -> str | None:
        """Takes: the first bytes of a file.
        Returns: the file's MIME type (for example "application/pdf"), or None if the
        type isn't recognized.
        """
        kind = filetype.guess(header)
        return None if kind is None else kind.mime
