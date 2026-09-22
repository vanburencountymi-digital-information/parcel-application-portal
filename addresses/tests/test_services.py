from __future__ import annotations

from unittest.mock import MagicMock

from django.test import TestCase

from addresses.models import Address
from addresses.services.address_service import AddressService
from addresses.services.exceptions import AddressVerificationError


class AddressServiceTests(TestCase):
    def _make_address(self) -> Address:
        return Address(
            line1="123 Main St",
            city="Springfield",
            state="IL",
            zip_code="62701",
        )

    def test_verify_saves_standardized_fields_on_success(self) -> None:
        standardized = {
            "line1": "123 MAIN ST",
            "line2": "",
            "city": "SPRINGFIELD",
            "state": "IL",
            "zip_code": "62701-1234",
        }
        mock_client = MagicMock()
        mock_client.standardize_address.return_value = standardized
        address = self._make_address()

        result = AddressService(address_client=mock_client).verify(address)

        self.assertEqual(result, standardized)
        address.refresh_from_db()
        self.assertTrue(address.is_verified)
        self.assertIsNotNone(address.verified_at)
        self.assertEqual(address.standardized_line1, "123 MAIN ST")
        self.assertEqual(address.standardized_zip_code, "62701-1234")

    def test_verify_saves_unverified_address_on_failure(self) -> None:
        mock_client = MagicMock()
        mock_client.standardize_address.side_effect = AddressVerificationError("boom")
        address = self._make_address()

        with self.assertRaises(AddressVerificationError):
            AddressService(address_client=mock_client).verify(address)

        address.refresh_from_db()
        self.assertFalse(address.is_verified)
        self.assertIsNone(address.verified_at)
