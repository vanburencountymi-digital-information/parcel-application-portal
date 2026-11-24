from django.test import TestCase
from django.urls import reverse

from assessing.models import AssessingUnit, Assessor
from assessing.tests.factories import AssessingUnitFactory, AssessorFactory
from authentication.models import User


class AdminTestCase(TestCase):
    admin_user: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_user = User.objects.create_superuser("admin@example.com", password="x")

    def setUp(self) -> None:
        self.client.force_login(self.admin_user)


class AssessingUnitAdminTests(AdminTestCase):
    def add_unit(self, name: str) -> None:
        response = self.client.post(
            reverse("admin:assessing_assessingunit_add"),
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


class AssessorAdminTests(AdminTestCase):
    unit: AssessingUnit

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.unit = AssessingUnitFactory.create()

    def add_data(self, email: str) -> dict[str, object]:
        return {
            "email": email,
            "first_name": "Ada",
            "last_name": "Lovelace",
            "phone_number": "",
            "assessing_units": [self.unit.pk],
            "is_active": "on",
        }

    def test_add_form_creates_user_and_assessor(self) -> None:
        response = self.client.post(
            reverse("admin:assessing_assessor_add"), self.add_data("Ada@Example.com")
        )

        self.assertEqual(response.status_code, 302)
        assessor = Assessor.objects.get()
        self.assertEqual(assessor.email, "ada@example.com")
        self.assertEqual(assessor.full_name, "Ada Lovelace")
        self.assertFalse(assessor.user.has_usable_password())
        self.assertEqual(list(assessor.assessing_units.all()), [self.unit])

    def test_duplicate_email_is_shown_as_a_form_error(self) -> None:
        AssessorFactory.create(user__email="ada@example.com")

        response = self.client.post(
            reverse("admin:assessing_assessor_add"), self.add_data("ADA@example.com")
        )

        self.assertContains(response, "email: User with this Email address already exists.")
        self.assertEqual(Assessor.objects.count(), 1)

    def test_change_form_updates_active_flag(self) -> None:
        assessor = AssessorFactory.create(assessing_units=[self.unit])

        response = self.client.post(
            reverse("admin:assessing_assessor_change", args=[assessor.pk]),
            {"phone_number": "", "assessing_units": [self.unit.pk]},
        )

        self.assertEqual(response.status_code, 302)
        assessor.refresh_from_db()
        self.assertFalse(assessor.is_active)
