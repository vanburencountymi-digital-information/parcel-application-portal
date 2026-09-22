from __future__ import annotations

from django.test import TestCase

from addresses.models import Address


class AddressTests(TestCase):
    def test_str_includes_line1_city_state_zip(self) -> None:
        address = Address(
            line1="123 Main St",
            city="Springfield",
            state="IL",
            zip_code="62701",
        )

        self.assertEqual(str(address), "123 Main St, Springfield, IL 62701")

    def test_defaults_to_unverified(self) -> None:
        address = Address.objects.create(
            line1="123 Main St",
            city="Springfield",
            state="IL",
            zip_code="62701",
        )

        self.assertFalse(address.is_verified)
        self.assertIsNone(address.verified_at)
        self.assertEqual(address.standardized_line1, "")
        self.assertEqual(address.standardized_zip_code, "")

    def test_verbose_name_plural_is_addresses(self) -> None:
        self.assertEqual(Address._meta.verbose_name_plural, "addresses")
