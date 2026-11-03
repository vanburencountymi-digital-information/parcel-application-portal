from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import requests
from django.test import SimpleTestCase, override_settings
from parameterized import parameterized

from parcels.client import ParcelClient
from parcels.exceptions import ParcelNotFoundError, ParcelServiceError
from parcels.types import ParcelDetail, ParcelSearchResult

BASE_URL = "https://parcels.example.test"

SEARCH_ROW = {
    "id": 56408,
    "parcel_no": "80-99-035-009-40",
    "address": "MAIN ST",
    "owner": "TEST OWNER & SPOUSE TRUST",
    "city": "TESTVILLE",
    "zip": "49064",
}

DETAIL: dict[str, Any] = {
    "type": "Feature",
    "properties": {
        "parcel_no": "80-99-035-009-40",
        "address": "MAIN ST",
        "city": "TESTVILLE",
        "state": "MI",
        "zip": "49064",
        "owner_name": "TEST OWNER & SPOUSE TRUST",
        "owner_address": "6 TEST CT",
        "owner_city": "BOLINGBROOK",
        "owner_state": "IL",
        "owner_zip": 60490,
        "acres": 1.5,
        "class": "402",
    },
    "geometry": {"type": "MultiPolygon", "coordinates": []},
}


def _response(*, status: int = 200, payload: Any = None, bad_json: bool = False) -> MagicMock:
    response = MagicMock(spec=requests.Response)
    response.status_code = status
    response.ok = status < 400
    if bad_json:
        response.json.side_effect = ValueError("not json")
    else:
        response.json.return_value = payload
    return response


def _client(
    response: MagicMock | None = None, *, error: Exception | None = None, **overrides: Any
) -> tuple[ParcelClient, MagicMock]:
    """A ParcelClient wired to a fake session. Returns the client and the fake session."""
    session = MagicMock(spec=requests.Session)
    if error is not None:
        session.get.side_effect = error
    else:
        session.get.return_value = response
    options: dict[str, Any] = {"base_url": BASE_URL, "token": "", "timeout": 7, **overrides}
    return ParcelClient(session=session, **options), session


class ParcelClientSearchTests(SimpleTestCase):
    def test_returns_search_results(self) -> None:
        client, session = _client(
            _response(payload={"count": 1, "results": [SEARCH_ROW]}),
            base_url=f"{BASE_URL}/",
        )

        results = client.search_parcels_by_text("  main  ", limit=5)

        self.assertEqual(
            results,
            [
                ParcelSearchResult(
                    id=56408,
                    parcel_no="80-99-035-009-40",
                    address="MAIN ST",
                    owner_name="TEST OWNER & SPOUSE TRUST",
                    city="TESTVILLE",
                    zip_code="49064",
                )
            ],
        )
        session.get.assert_called_once_with(
            f"{BASE_URL}/api/parcels/search",
            params={"q": "main", "limit": 5},
            headers={},
            timeout=7,
        )

    @parameterized.expand(
        [
            ("too_short", "a", 15),
            ("blank", "   ", 15),
            ("limit_too_low", "main", 0),
            ("limit_too_high", "main", 51),
        ]
    )
    def test_rejects_bad_input_without_calling_the_service(
        self, _name: str, query: str, limit: int
    ) -> None:
        client, session = _client(_response(payload={"results": []}))

        with self.assertRaises(ValueError):
            client.search_parcels_by_text(query, limit=limit)

        session.get.assert_not_called()

    @parameterized.expand(
        [
            ("missing_results", {"count": 0}),
            ("row_without_id", {"results": [{"parcel_no": "80-99-1"}]}),
            ("not_a_dict", ["unexpected"]),
        ]
    )
    def test_unexpected_response_raises(self, _name: str, payload: Any) -> None:
        client, _session = _client(_response(payload=payload))

        with self.assertRaises(ParcelServiceError):
            client.search_parcels_by_text("main")


class ParcelClientGetTests(SimpleTestCase):
    def test_returns_parcel_detail(self) -> None:
        client, session = _client(_response(payload=DETAIL))

        parcel = client.get_parcel_by_id(56408)

        self.assertEqual(
            parcel,
            ParcelDetail(
                id=56408,
                parcel_no="80-99-035-009-40",
                address="MAIN ST",
                city="TESTVILLE",
                state="MI",
                zip_code="49064",
                owner_name="TEST OWNER & SPOUSE TRUST",
                owner_address="6 TEST CT",
                owner_city="BOLINGBROOK",
                owner_state="IL",
                owner_zip_code="60490",
                acres=1.5,
                property_class="402",
                geometry={"type": "MultiPolygon", "coordinates": []},
            ),
        )
        self.assertEqual(session.get.call_args.args[0], f"{BASE_URL}/api/parcels/56408")

    def test_restores_leading_zero_on_integer_zip(self) -> None:
        detail = {**DETAIL, "properties": {**DETAIL["properties"], "owner_zip": 2134}}
        client, _session = _client(_response(payload=detail))

        self.assertEqual(client.get_parcel_by_id(1).owner_zip_code, "02134")

    def test_missing_acres_and_geometry_are_none(self) -> None:
        properties = {k: v for k, v in DETAIL["properties"].items() if k != "acres"}
        client, _session = _client(_response(payload={"properties": properties}))

        parcel = client.get_parcel_by_id(1)

        self.assertIsNone(parcel.acres)
        self.assertIsNone(parcel.geometry)

    @parameterized.expand(
        [
            ("text_with_dash", "49026-9606"),
            ("digit_string", "56408"),
            ("negative", -1),
            ("empty", ""),
            ("sql", "1; DROP TABLE geo.parcels"),
            ("float", 5.0),
            ("none", None),
            ("bool", True),
        ]
    )
    def test_rejects_anything_but_a_non_negative_int_without_calling_the_service(
        self, _name: str, parcel_id: Any
    ) -> None:
        client, session = _client(_response(payload=DETAIL))

        with self.assertRaises(ValueError):
            client.get_parcel_by_id(parcel_id)

        session.get.assert_not_called()

    def test_404_raises_not_found(self) -> None:
        client, _session = _client(_response(status=404))

        with self.assertRaises(ParcelNotFoundError):
            client.get_parcel_by_id(1)

    def test_other_error_statuses_are_not_reported_as_not_found(self) -> None:
        client, _session = _client(_response(status=429))

        with self.assertRaises(ParcelServiceError) as raised:
            client.get_parcel_by_id(1)

        self.assertNotIsInstance(raised.exception, ParcelNotFoundError)
        self.assertEqual(raised.exception.status_code, 429)

    def test_missing_parcel_no_raises(self) -> None:
        client, _session = _client(_response(payload={"properties": {"address": "MAIN ST"}}))

        with self.assertRaises(ParcelServiceError):
            client.get_parcel_by_id(1)


class ParcelClientRequestTests(SimpleTestCase):
    @parameterized.expand(
        [
            ("timeout", requests.Timeout("slow")),
            ("connection_error", requests.ConnectionError("refused")),
        ]
    )
    def test_network_errors_raise_service_error(self, _name: str, error: Exception) -> None:
        client, _session = _client(error=error)

        with self.assertRaises(ParcelServiceError) as raised:
            client.search_parcels_by_text("main")

        self.assertIsNone(raised.exception.status_code)

    @parameterized.expand([("server_error", 500), ("unauthorized", 401), ("bad_gateway", 502)])
    def test_error_status_raises_service_error_with_the_status(
        self, _name: str, status: int
    ) -> None:
        client, _session = _client(_response(status=status))

        with self.assertRaises(ParcelServiceError) as raised:
            client.search_parcels_by_text("main")

        self.assertEqual(raised.exception.status_code, status)

    def test_non_json_response_raises_service_error(self) -> None:
        client, _session = _client(_response(bad_json=True))

        with self.assertRaises(ParcelServiceError):
            client.search_parcels_by_text("main")

    def test_404_on_search_is_a_plain_service_error(self) -> None:
        client, _session = _client(_response(status=404))

        with self.assertRaises(ParcelServiceError) as raised:
            client.search_parcels_by_text("main")

        self.assertNotIsInstance(raised.exception, ParcelNotFoundError)
        self.assertEqual(raised.exception.status_code, 404)

    def test_sends_bearer_token_when_configured(self) -> None:
        client, session = _client(_response(payload={"results": []}), token="secret-token")

        client.search_parcels_by_text("main")

        self.assertEqual(
            session.get.call_args.kwargs["headers"], {"Authorization": "Bearer secret-token"}
        )

    def test_unset_url_raises_without_calling_the_service(self) -> None:
        client, session = _client(_response(payload={"results": []}), base_url="")

        with self.assertRaises(ParcelServiceError):
            client.search_parcels_by_text("main")

        session.get.assert_not_called()


class ParcelClientSettingsTests(SimpleTestCase):
    """With no arguments, the client takes its URL, token and timeout from the settings."""

    @override_settings(
        PARCEL_SERVICE_URL="https://from-settings.example.test/",
        PARCEL_SERVICE_TOKEN="settings-token",
        PARCEL_SERVICE_TIMEOUT=3,
    )
    def test_defaults_come_from_settings(self) -> None:
        session = MagicMock(spec=requests.Session)
        session.get.return_value = _response(payload={"results": []})

        ParcelClient(session=session).search_parcels_by_text("main")

        session.get.assert_called_once_with(
            "https://from-settings.example.test/api/parcels/search",
            params={"q": "main", "limit": 15},
            headers={"Authorization": "Bearer settings-token"},
            timeout=3,
        )

    @override_settings(
        PARCEL_SERVICE_URL="https://from-settings.example.test",
        PARCEL_SERVICE_TOKEN="settings-token",
    )
    def test_arguments_win_over_settings_even_when_empty(self) -> None:
        session = MagicMock(spec=requests.Session)
        session.get.return_value = _response(payload={"results": []})

        ParcelClient(base_url=BASE_URL, token="", session=session).search_parcels_by_text("main")

        self.assertEqual(session.get.call_args.args[0], f"{BASE_URL}/api/parcels/search")
        self.assertEqual(session.get.call_args.kwargs["headers"], {})
