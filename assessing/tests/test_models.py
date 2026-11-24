from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import SimpleTestCase, TestCase
from parameterized import parameterized

from assessing.models import AssessingUnit, Assessor
from assessing.tests.factories import AssessingUnitFactory, AssessorFactory


class AssessingUnitStrTests(SimpleTestCase):
    @parameterized.expand(
        [
            ("township", AssessingUnit.Kind.TOWNSHIP, "Paw Paw (Township)"),
            ("city", AssessingUnit.Kind.CITY, "Paw Paw (City)"),
        ]
    )
    def test_str_includes_kind(self, _name: str, kind: str, expected: str) -> None:
        self.assertEqual(str(AssessingUnitFactory.build(name="Paw Paw", kind=kind)), expected)


class AssessingUnitConstraintTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        AssessingUnitFactory(name="Paw Paw", parcel_unit_code="80")

    def test_same_name_and_kind_is_rejected(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            AssessingUnitFactory(name="Paw Paw")

    def test_same_name_in_different_case_is_rejected(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            AssessingUnitFactory(name="paw paw")

    def test_same_name_with_different_kind_is_allowed(self) -> None:
        AssessingUnitFactory(name="Paw Paw", kind=AssessingUnit.Kind.CITY)
        self.assertEqual(AssessingUnit.objects.filter(name="Paw Paw").count(), 2)

    def test_unit_code_must_be_unique(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            AssessingUnitFactory(parcel_unit_code="80")

    def test_blank_unit_codes_can_repeat(self) -> None:
        AssessingUnitFactory.create_batch(2)
        self.assertEqual(AssessingUnit.objects.filter(parcel_unit_code__isnull=True).count(), 2)


class AssessorTests(TestCase):
    unit: AssessingUnit
    active: Assessor

    @classmethod
    def setUpTestData(cls) -> None:
        cls.unit = AssessingUnitFactory.create()
        cls.active = AssessorFactory.create(assessing_units=[cls.unit])

    def test_units_are_linked(self) -> None:
        self.assertEqual(list(self.active.assessing_units.all()), [self.unit])

    def test_user_with_an_assessor_cannot_be_deleted(self) -> None:
        with self.assertRaises(ProtectedError):
            self.active.user.delete()

    def test_name_and_email_come_from_the_user(self) -> None:
        user = self.active.user
        self.assertEqual(
            (self.active.email, self.active.first_name, self.active.last_name),
            (user.email, user.first_name, user.last_name),
        )
        self.assertEqual(self.active.full_name, user.get_full_name())

    def test_assessors_are_ordered_by_email(self) -> None:
        AssessorFactory.create(user__email="zed@example.com")
        AssessorFactory.create(user__email="amy@example.com")

        emails = [assessor.email for assessor in Assessor.objects.all()]

        self.assertEqual(emails, sorted(emails))

    def test_with_unit_creates_a_unit(self) -> None:
        assessor = AssessorFactory.create(with_unit=True)
        self.assertEqual(assessor.assessing_units.count(), 1)

    def test_units_can_be_passed_as_pks(self) -> None:
        assessor = AssessorFactory.create(assessing_units=[self.unit.pk])
        self.assertEqual(list(assessor.assessing_units.all()), [self.unit])

    def test_no_units_by_default(self) -> None:
        self.assertEqual(AssessorFactory.create().assessing_units.count(), 0)

    def test_phone_number_is_optional(self) -> None:
        self.assertEqual(str(self.active.phone_number), "")

    def test_a_us_number_without_country_code_is_accepted(self) -> None:
        assessor = AssessorFactory.create(phone_number="269-555-0142")
        assessor.refresh_from_db()
        self.assertEqual(assessor.phone_number.as_e164, "+12695550142")


class AssessorStrTests(SimpleTestCase):
    @parameterized.expand(
        [
            ("name", "Ada", "Lovelace", "Ada Lovelace"),
            ("email_only", "", "", "ada@example.com"),
        ]
    )
    def test_str(self, _name: str, first: str, last: str, expected: str) -> None:
        assessor = AssessorFactory.build(
            user__first_name=first, user__last_name=last, user__email="ada@example.com"
        )
        self.assertEqual(str(assessor), expected)
