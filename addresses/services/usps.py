"""USPS Addresses API v3 client — OAuth2 client-credentials + address standardization.

The old USPS Web Tools XML API shut down January 2026; this targets the current
REST API at https://apis.usps.com (see https://developers.usps.com/apis).
"""

from __future__ import annotations

import requests
from django.conf import settings

from .exceptions import AddressVerificationError


class USPSClient:
    """Thin client for the USPS Addresses API v3. Caches its OAuth2 access
    token for the lifetime of the client instance, rather than re-authenticating
    on every call.
    """

    def __init__(self) -> None:
        self._access_token: str | None = None

    def _get_access_token(self) -> str:
        if self._access_token is not None:
            return self._access_token

        response = requests.post(
            f"{settings.USPS_API_BASE_URL}/oauth2/v3/token",
            json={
                "grant_type": "client_credentials",
                "client_id": settings.USPS_CLIENT_ID,
                "client_secret": settings.USPS_CLIENT_SECRET,
            },
            timeout=10,
        )
        if not response.ok:
            raise AddressVerificationError(
                f"USPS OAuth token request failed: {response.status_code} {response.text}"
            )
        self._access_token = response.json()["access_token"]
        return self._access_token

    def standardize_address(
        self, *, line1: str, line2: str, city: str, state: str, zip_code: str
    ) -> dict[str, str]:
        """Standardize/verify a US address against USPS. Returns the standardized fields."""
        token = self._get_access_token()
        response = requests.get(
            f"{settings.USPS_API_BASE_URL}/addresses/v3/address",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "streetAddress": line1,
                "secondaryAddress": line2,
                "city": city,
                "state": state,
                "ZIPCode": zip_code,
            },
            timeout=10,
        )
        if not response.ok:
            raise AddressVerificationError(
                f"USPS address standardization failed: {response.status_code} {response.text}"
            )

        address = response.json().get("address", {})
        return {
            "line1": address.get("streetAddress", line1),
            "line2": address.get("secondaryAddress", line2),
            "city": address.get("city", city),
            "state": address.get("state", state),
            "zip_code": address.get("ZIPCode", zip_code),
        }
