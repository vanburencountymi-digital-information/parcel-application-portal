class DocumentValidationError(ValueError):
    """The upload was refused (wrong type, too big, empty, or a bad folder).

    The message is written for the person uploading, so views can show it as-is.
    """
