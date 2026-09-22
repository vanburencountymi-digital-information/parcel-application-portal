from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import requests
from django.test import SimpleTestCase
from parameterized import parameterized

from addresses.services.census import CensusGeocoderClient
from addresses.services.exceptions import AddressVerificationError

ADDRESS = {
    "line1": "4600 Silver Hill Rd",
    "line2": "Ste 100",
    "city": "Washington",
    "state": "DC",
    "zip_code": "20233",
}

MATCH = {
    "matchedAddress": "4600 SILVER HILL RD, WASHINGTON, DC, 20233",
    "addressComponents": {
        "city": "WASHINGTON",
        "state": "DC",
        "zip": "20233",
    },
}


def _response(*, ok: bool = True, matches: list[dict[str, Any]] | None = None) -> MagicMock:
    response = MagicMock(spec=requests.Response)
    response.ok = ok
    response.status_code = 200 if ok else 400
    response.text = "bad request"
    response.json.return_value = {"result": {"addressMatches": matches or []}}
    return response


class CensusGeocoderClientTests(SimpleTestCase):
    @patch("addresses.services.census.requests.get", autospec=True)
    def test_returns_standardized_fields_for_single_match(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _response(matches=[MATCH])

        result = CensusGeocoderClient().standardize_address(**ADDRESS)

        self.assertEqual(
            result,
            {
                "line1": "4600 SILVER HILL RD",
                "line2": "Ste 100",
                "city": "WASHINGTON",
                "state": "DC",
                "zip_code": "20233",
            },
        )

    @parameterized.expand(
        [
            ("no_match", _response(matches=[]), None, "No matching address"),
            ("ambiguous", _response(matches=[MATCH, MATCH]), None, "ambiguous"),
            ("http_error", _response(ok=False), None, "400"),
            ("network_error", None, requests.ConnectionError("down"), "down"),
        ]
    )
    @patch("addresses.services.census.requests.get", autospec=True)
    def test_raises_verification_error(
        self,
        _name: str,
        response: MagicMock | None,
        error: Exception | None,
        message: str,
        mock_get: MagicMock,
    ) -> None:
        mock_get.return_value = response
        mock_get.side_effect = error

        with self.assertRaisesMessage(AddressVerificationError, message):
            CensusGeocoderClient().standardize_address(**ADDRESS)
