from __future__ import annotations

from typing import Any

from django.test import SimpleTestCase
from parameterized import parameterized

from parcels.serializers import (
    ParcelDetailSerializer,
    ParcelSearchResponseSerializer,
    ZipCodeField,
)
from parcels.types import ParcelDetail, ParcelSearchResult

PROPERTIES: dict[str, Any] = {
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
}
GEOMETRY = {"type": "MultiPolygon", "coordinates": []}


def _detail(payload: dict[str, Any]) -> ParcelDetailSerializer:
    return ParcelDetailSerializer(data=payload, parcel_id=56408)


class ZipCodeFieldTests(SimpleTestCase):
    @parameterized.expand(
        [
            ("string", "49064", "49064"),
            ("integer", 60490, "60490"),
            ("integer_lost_leading_zero", 2134, "02134"),
            ("string_lost_leading_zero", "2134", "02134"),
            ("zip_plus_four_left_alone", "49064-1234", "49064-1234"),
            ("non_ascii_digits_left_alone", "\u0663\u0664", "\u0663\u0664"),
            ("superscript_digits_left_alone", "\u00b2\u00b3", "\u00b2\u00b3"),
            ("blank", "", ""),
            ("null", None, ""),
        ]
    )
    def test_cleans_up_zip_codes(self, _name: str, value: Any, expected: str) -> None:
        self.assertEqual(ZipCodeField().run_validation(value), expected)

    def test_missing_zip_is_blank(self) -> None:
        self.assertEqual(ZipCodeField().run_validation(), "")


class ParcelSearchResponseSerializerTests(SimpleTestCase):
    def test_save_returns_search_results_with_owner_renamed(self) -> None:
        serializer = ParcelSearchResponseSerializer(
            data={
                "count": 1,
                "results": [
                    {
                        "id": 56408,
                        "parcel_no": "80-99-035-009-40",
                        "address": "MAIN ST",
                        "owner": "TEST OWNER & SPOUSE TRUST",
                        "city": "TESTVILLE",
                        "zip": "49064",
                    }
                ],
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.save(),
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

    def test_missing_and_null_text_become_blank(self) -> None:
        serializer = ParcelSearchResponseSerializer(
            data={"results": [{"id": 1, "parcel_no": "80-99-1", "address": None, "zip": None}]}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        result = serializer.save()[0]
        self.assertEqual(
            (result.address, result.owner_name, result.city, result.zip_code), ("", "", "", "")
        )

    def test_no_results_is_an_empty_list(self) -> None:
        serializer = ParcelSearchResponseSerializer(data={"count": 0, "results": []})

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.save(), [])

    @parameterized.expand(
        [
            ("missing_results", {"count": 0}),
            ("results_not_a_list", {"results": "nope"}),
            ("row_without_id", {"results": [{"parcel_no": "80-99-1"}]}),
            ("row_without_parcel_no", {"results": [{"id": 1}]}),
            ("id_not_a_number", {"results": [{"id": "abc", "parcel_no": "80-99-1"}]}),
            ("not_a_dict", ["unexpected"]),
        ]
    )
    def test_rejects_bad_shapes(self, _name: str, payload: Any) -> None:
        self.assertFalse(ParcelSearchResponseSerializer(data=payload).is_valid())


class ParcelDetailSerializerTests(SimpleTestCase):
    def test_save_returns_parcel_detail(self) -> None:
        serializer = _detail({"type": "Feature", "properties": PROPERTIES, "geometry": GEOMETRY})

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.save(),
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
                geometry=GEOMETRY,
            ),
        )

    def test_restores_the_leading_zero_on_an_integer_owner_zip(self) -> None:
        serializer = _detail({"properties": {**PROPERTIES, "owner_zip": 2134}})

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.save().owner_zip_code, "02134")

    @parameterized.expand([("missing", None), ("null", "null")])
    def test_missing_acres_and_geometry_are_none(self, name: str, _marker: Any) -> None:
        properties = {k: v for k, v in PROPERTIES.items() if k != "acres"}
        payload: dict[str, Any] = {"properties": properties}
        if name == "null":
            payload = {"properties": {**properties, "acres": None}, "geometry": None}
        serializer = _detail(payload)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        parcel = serializer.save()
        self.assertIsNone(parcel.acres)
        self.assertIsNone(parcel.geometry)

    def test_zero_acres_is_kept_not_treated_as_missing(self) -> None:
        serializer = _detail({"properties": {**PROPERTIES, "acres": 0}})

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.save().acres, 0.0)

    @parameterized.expand(
        [
            ("no_properties", {"geometry": GEOMETRY}),
            ("no_parcel_no", {"properties": {"address": "MAIN ST"}}),
            ("properties_not_a_dict", {"properties": "nope"}),
            ("acres_not_a_number", {"properties": {**PROPERTIES, "acres": "lots"}}),
            ("not_a_dict", ["unexpected"]),
        ]
    )
    def test_rejects_bad_shapes(self, _name: str, payload: Any) -> None:
        self.assertFalse(_detail(payload).is_valid())

    def test_errors_do_not_echo_the_data(self) -> None:
        serializer = _detail({"properties": {**PROPERTIES, "parcel_no": None}})

        self.assertFalse(serializer.is_valid())
        self.assertNotIn("TEST OWNER", str(serializer.errors))
