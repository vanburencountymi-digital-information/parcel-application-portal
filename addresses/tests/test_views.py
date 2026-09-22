from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.urls import reverse

from addresses.models import Address
from addresses.services.exceptions import AddressVerificationError

VALID_FORM_DATA = {
    "line1": "123 Main St",
    "line2": "",
    "city": "Springfield",
    "state": "IL",
    "zip_code": "62701",
}


class HomeViewTests(TestCase):
    def test_home_renders(self) -> None:
        response = self.client.get(reverse("addresses:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "addresses/home.html")


class AddressFormViewTests(TestCase):
    def test_get_renders_empty_form(self) -> None:
        response = self.client.get(reverse("addresses:address-form"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "addresses/address_form.html")

    @patch("addresses.views.AddressService.verify")
    def test_post_valid_data_shows_standardized_result(self, mock_verify: MagicMock) -> None:
        mock_verify.return_value = {
            "line1": "123 MAIN ST",
            "line2": "",
            "city": "SPRINGFIELD",
            "state": "IL",
            "zip_code": "62701-1234",
        }

        response = self.client.post(reverse("addresses:address-form"), VALID_FORM_DATA)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["result"], mock_verify.return_value)
        self.assertIsNone(response.context["error"])
        mock_verify.assert_called_once()

    @patch("addresses.views.AddressService.verify")
    def test_post_shows_error_when_verification_fails(self, mock_verify: MagicMock) -> None:
        mock_verify.side_effect = AddressVerificationError("USPS is unavailable")

        response = self.client.post(reverse("addresses:address-form"), VALID_FORM_DATA)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["result"])
        self.assertEqual(response.context["error"], "USPS is unavailable")

    def test_post_invalid_data_reshows_form_with_errors(self) -> None:
        response = self.client.post(reverse("addresses:address-form"), {})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(Address.objects.count(), 0)
