from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from parameterized import parameterized

from applications.exceptions import AssessorValidationError
from applications.models import AssessingUnit, Assessor
from applications.services import AssessorService
from applications.tests.factories import AssessingUnitFactory, AssessorFactory
from authentication.models import User
from common.tests.factories import UserFactory


class AssessorServiceCreateTests(TestCase):
    units: list[AssessingUnit]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.units = AssessingUnitFactory.create_batch(2)

    def test_creates_user_and_assessor(self) -> None:
        assessor = AssessorService().create(
            "Ada@Example.com ", self.units, first_name="Ada", last_name="Lovelace"
        )

        user = assessor.user
        self.assertEqual(user.email, "ada@example.com")
        self.assertEqual((user.first_name, user.last_name), ("Ada", "Lovelace"))
        self.assertFalse(user.has_usable_password())
        self.assertTrue(assessor.is_active)
        self.assertCountEqual(assessor.assessing_units.all(), self.units)

    def test_can_create_an_inactive_assessor_with_no_units(self) -> None:
        assessor = AssessorService().create("ada@example.com", [], is_active=False)

        self.assertFalse(assessor.is_active)
        self.assertEqual(assessor.assessing_units.count(), 0)

    @parameterized.expand(
        [
            ("us_without_country_code", "269-555-0142", "+12695550142"),
            ("with_country_code", "+1 269 555 0142", "+12695550142"),
        ]
    )
    def test_phone_number_is_normalized(self, _name: str, given: str, expected: str) -> None:
        assessor = AssessorService().create("ada@example.com", [], phone_number=given)
        assessor.refresh_from_db()

        self.assertEqual(assessor.phone_number.as_e164, expected)

    @parameterized.expand([("letters", "not a number"), ("too_short", "555")])
    def test_bad_phone_number_saves_nothing(self, _name: str, given: str) -> None:
        with self.assertRaisesMessage(AssessorValidationError, "phone_number:"):
            AssessorService().create("ada@example.com", self.units, phone_number=given)

        self.assertFalse(User.objects.filter(email="ada@example.com").exists())
        self.assertEqual(Assessor.objects.count(), 0)

    @parameterized.expand(
        [("empty", ""), ("spaces", "   "), ("no_domain", "ada@"), ("no_at", "ada")]
    )
    def test_bad_email_is_rejected(self, _name: str, given: str) -> None:
        with self.assertRaisesMessage(AssessorValidationError, "email:"):
            AssessorService().create(given, self.units)

    @parameterized.expand(
        [
            ("same_case", "ada@example.com"),
            ("different_case", "ADA@Example.COM"),
            ("padded", " ada@example.com "),
        ]
    )
    def test_duplicate_email_is_rejected_ignoring_case(self, _name: str, given: str) -> None:
        AssessorFactory.create(user__email="ada@example.com")

        with self.assertRaisesMessage(AssessorValidationError, "already exists"):
            AssessorService().create(given, self.units)

        self.assertEqual(Assessor.objects.count(), 1)

    def test_email_already_used_by_a_non_assessor_user_is_rejected(self) -> None:
        UserFactory.create(email="Walter@Example.com")

        with self.assertRaisesMessage(AssessorValidationError, "already exists"):
            AssessorService().create("walter@example.com", self.units)

    @patch("applications.services.Assessor.save", autospec=True, side_effect=RuntimeError("boom"))
    def test_failure_after_the_user_is_saved_saves_nothing(self, _save: MagicMock) -> None:
        with self.assertRaises(RuntimeError):
            AssessorService().create("ada@example.com", self.units)

        self.assertFalse(User.objects.filter(email="ada@example.com").exists())
        self.assertEqual(Assessor.objects.count(), 0)

    @patch("applications.services.User.full_clean", autospec=True)
    def test_database_email_clash_is_reported_as_a_duplicate(self, _full_clean: MagicMock) -> None:
        # Skipping full_clean stands in for losing a race: the database is what refuses.
        UserFactory.create(email="ada@example.com")

        with self.assertRaisesMessage(AssessorValidationError, "already exists"):
            AssessorService().create("ada@example.com", self.units)

        self.assertEqual(Assessor.objects.count(), 0)

    @patch(
        "applications.services.User.save",
        side_effect=IntegrityError("some other constraint"),
    )
    def test_other_database_errors_are_not_hidden(self, _create: MagicMock) -> None:
        with self.assertRaisesMessage(IntegrityError, "some other constraint"):
            AssessorService().create("ada@example.com", self.units)

    @patch("applications.services.User.clean", side_effect=ValidationError("No can do."))
    def test_errors_with_no_field_are_shown_without_a_prefix(self, _clean: MagicMock) -> None:
        with self.assertRaises(AssessorValidationError) as raised:
            AssessorService().create("ada@example.com", self.units)

        self.assertEqual(str(raised.exception), "No can do.")
