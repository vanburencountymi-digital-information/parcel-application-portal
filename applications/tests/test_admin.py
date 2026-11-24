from django.test import TestCase
from django.urls import reverse

from applications.models import AssessingUnit
from authentication.models import User


class AssessingUnitAdminTests(TestCase):
    admin_user: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_user = User.objects.create_superuser("admin@example.com", password="x")

    def setUp(self) -> None:
        self.client.force_login(self.admin_user)

    def add_unit(self, name: str) -> None:
        response = self.client.post(
            reverse("admin:applications_assessingunit_add"),
            {"name": name, "kind": AssessingUnit.Kind.TOWNSHIP, "parcel_unit_code": ""},
        )
        self.assertEqual(response.status_code, 302)

    def test_blank_unit_code_is_saved_as_null(self) -> None:
        self.add_unit("Antwerp")

        self.assertIsNone(AssessingUnit.objects.get(name="Antwerp").parcel_unit_code)

    def test_two_units_can_both_have_no_unit_code(self) -> None:
        self.add_unit("Antwerp")
        self.add_unit("Bangor")

        self.assertEqual(AssessingUnit.objects.filter(parcel_unit_code__isnull=True).count(), 2)
