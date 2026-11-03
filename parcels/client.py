"""Client for the county parcel service (land-division-portal-v2).

The parcel service is the source of truth for parcels. It is read-only from here.
The client only checks its inputs and fetches; turning responses into our own types is
the serializers' job (parcels/serializers.py). Its URL, token and timeout default to
settings, so switching to the authenticated endpoint is a settings change.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

import requests
from django.conf import settings
from rest_framework import serializers

from .exceptions import ParcelNotFoundError, ParcelServiceError
from .serializers import ParcelDetailSerializer, ParcelSearchResponseSerializer
from .types import ParcelDetail, ParcelSearchResult

MIN_QUERY_LENGTH = 2
MAX_SEARCH_LIMIT = 50

# Routes on the parcel service. Appended to PARCEL_SERVICE_URL; if the authenticated
# version moves under a prefix like /v2, put that prefix in the URL setting instead.
SEARCH_PATH = "/api/parcels/search"
DETAIL_PATH = "/api/parcels/{parcel_id}"


class ParcelClient:
    """Thin client for the parcel service's search and detail endpoints."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        token: str | None = None,
        timeout: float | None = None,
        session: requests.Session | None = None,
    ) -> None:
        """Takes: `base_url`, `token` and `timeout` (seconds), which default to the settings
        PARCEL_SERVICE_URL, PARCEL_SERVICE_TOKEN and PARCEL_SERVICE_TIMEOUT, and an optional
        `requests.Session` to send requests with (tests pass a fake one).
        Returns: nothing. An empty `base_url` is allowed here and raises on the first request.
        """
        self._base_url = (settings.PARCEL_SERVICE_URL if base_url is None else base_url).rstrip("/")
        self._token = settings.PARCEL_SERVICE_TOKEN if token is None else token
        self._timeout = settings.PARCEL_SERVICE_TIMEOUT if timeout is None else timeout
        self._session = session if session is not None else requests.Session()

    def search_parcels_by_text(self, query: str, *, limit: int = 15) -> list[ParcelSearchResult]:
        """Find parcels by a piece of street address, owner, or parcel number.

        Takes: `query` (at least 2 characters once stripped) and `limit` (1 to 50).
        Returns: a list of `ParcelSearchResult`, empty when nothing matches.
        Raises: `ValueError` for a bad query or limit; `ParcelServiceError` if the service
        can't be reached, answers with an error, or sends something we can't read.
        """
        query = query.strip()
        self._verify_query_length(query)
        self._verify_limit(limit)

        payload = self._get(SEARCH_PATH, params={"q": query, "limit": limit})
        return self._parse_or_raise(ParcelSearchResponseSerializer(data=payload))

    def get_parcel_by_id(self, parcel_id: int) -> ParcelDetail:
        """Fetch one parcel by the parcel service's id.

        Takes: `parcel_id`, an int only. Callers holding text (a URL, a form) convert it
        first, with a `<int:...>` URL pattern or an IntegerField.
        Returns: the `ParcelDetail`.
        Raises: `ValueError` if `parcel_id` isn't a non-negative int; `ParcelNotFoundError`
        if the service has no such parcel; `ParcelServiceError` for any other failure.
        """
        self._verify_parcel_id(parcel_id)

        try:
            payload = self._get(DETAIL_PATH.format(parcel_id=parcel_id))
        except ParcelServiceError as exc:
            if exc.status_code == HTTPStatus.NOT_FOUND:
                raise ParcelNotFoundError("No parcel found with that id.") from exc
            raise
        return self._parse_or_raise(ParcelDetailSerializer(data=payload, parcel_id=parcel_id))

    @staticmethod
    def _parse_or_raise(serializer: serializers.BaseSerializer[Any]) -> Any:
        """Takes: a serializer built from a response. Returns: what its `save()` returns.
        Raises: `ParcelServiceError` if the response isn't valid.
        """
        if not serializer.is_valid():
            raise ParcelServiceError(f"Unexpected parcel service response: {serializer.errors}")
        return serializer.save()

    @staticmethod
    def _verify_query_length(query: str) -> None:
        """Takes: the stripped query. Raises: `ValueError` if it is too short."""
        if len(query) < MIN_QUERY_LENGTH:
            raise ValueError(f"Search needs at least {MIN_QUERY_LENGTH} characters.")

    @staticmethod
    def _verify_limit(limit: int) -> None:
        """Takes: the result limit. Raises: `ValueError` if it is outside 1 to 50."""
        if not 1 <= limit <= MAX_SEARCH_LIMIT:
            raise ValueError(f"limit must be between 1 and {MAX_SEARCH_LIMIT}.")

    @staticmethod
    def _verify_parcel_id(parcel_id: int) -> None:
        """Takes: a parcel id. Raises: `ValueError` unless it is a non-negative int."""
        # The parcel service doesn't reject non-integer ids: they reach its SQL and come back
        # as a 500, so a bad id must never leave this process. `type(...) is not int`, not
        # `isinstance`, because bool is a subclass of int and True would pass as parcel 1.
        if type(parcel_id) is not int or parcel_id < 0:
            raise ValueError(f"parcel_id must be a non-negative integer, got {parcel_id!r}.")

    def _build_url(self, path: str) -> str:
        """Takes: a route such as SEARCH_PATH. Returns: the full URL on the parcel service.
        Raises: `ParcelServiceError` if no base URL is configured.
        """
        if not self._base_url:
            raise ParcelServiceError("PARCEL_SERVICE_URL is not set.")
        return f"{self._base_url}{path}"

    def _build_headers(self) -> dict[str, str]:
        """Returns: the headers for a request, with the Bearer token when one is configured."""
        headers: dict[str, str] = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        """Takes: a route and optional query parameters. Returns: the decoded JSON.
        Raises: `ParcelServiceError` (with `status_code` set when the service answered with
        an error) if the request fails or the body isn't JSON.
        """
        try:
            response = self._session.get(
                self._build_url(path),
                params=params,
                headers=self._build_headers(),
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            raise ParcelServiceError(f"Parcel service request failed: {exc}") from exc

        if not response.ok:
            raise ParcelServiceError(
                f"Parcel service returned {response.status_code}.",
                status_code=response.status_code,
            )

        try:
            return response.json()
        except ValueError as exc:
            raise ParcelServiceError("Parcel service sent a response that isn't JSON.") from exc
