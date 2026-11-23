from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase
from parameterized import parameterized

from applications.models import AssessingUnit
from applications.tests.factories import AssessingUnitFactory


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
