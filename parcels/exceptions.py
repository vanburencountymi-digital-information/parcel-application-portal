class ParcelServiceError(Exception):
    """The parcel service could not be reached, or sent back something we can't use.

    ParcelClient raises this (and its subclasses) for every failure, so callers
    never need to know about `requests` or the service's response format.

    `status_code` is the HTTP status when the service answered with an error, else None.
    """

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ParcelNotFoundError(ParcelServiceError):
    """The parcel service has no parcel with the requested id."""
