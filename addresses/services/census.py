"""US Census Bureau Geocoder client — address matching/standardization.

Free, keyless, public-domain (https://geocoding.geo.census.gov/geocoder/). It
matches against TIGER address ranges, so a match means "this house number falls
on a real street segment", not USPS deliverability: it doesn't know about units
(line2 is passed through as entered) and only returns 5-digit ZIPs.
"""

from __future__ import annotations

import requests

from .exceptions import AddressVerificationError

CENSUS_GEOCODER_URL = "https://geocoding.geo.census.gov/geocoder/locations/address"


class CensusGeocoderClient:
    """Thin client for the Census Geocoder's single-address endpoint."""

    def standardize_address(
        self, *, line1: str, line2: str, city: str, state: str, zip_code: str
    ) -> dict[str, str]:
        """Match a US address against the Census Geocoder. Returns the standardized fields."""
        try:
            response = requests.get(
                CENSUS_GEOCODER_URL,
                params={
                    "street": line1,
                    "city": city,
                    "state": state,
                    "zip": zip_code,
                    "benchmark": "Public_AR_Current",
                    "format": "json",
                },
                timeout=10,
            )
        except requests.RequestException as exc:
            raise AddressVerificationError(f"Census Geocoder request failed: {exc}") from exc

        if not response.ok:
            raise AddressVerificationError(
                f"Census Geocoder request failed: {response.status_code} {response.text}"
            )

        matches = response.json().get("result", {}).get("addressMatches", [])
        if not matches:
            raise AddressVerificationError("No matching address found.")
        if len(matches) > 1:
            raise AddressVerificationError(
                "Address is ambiguous — it matched more than one location."
            )

        match = matches[0]
        components = match["addressComponents"]
        # matchedAddress is "STREET, CITY, ST, ZIP"; components only carry the
        # street segment's address range, not the matched house number.
        return {
            "line1": match["matchedAddress"].split(", ")[0],
            "line2": line2,
            "city": components["city"],
            "state": components["state"],
            "zip_code": components["zip"],
        }
