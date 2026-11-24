from django.test import TestCase
from django.urls import reverse

from authentication.models import User


class UserAdminTests(TestCase):
    admin_user: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_user = User.objects.create_superuser("admin@example.com", password="x")

    def setUp(self) -> None:
        self.client.force_login(self.admin_user)

    def test_add_page_loads(self) -> None:
        self.assertEqual(self.client.get(reverse("admin:authentication_user_add")).status_code, 200)

    def test_change_page_loads(self) -> None:
        url = reverse("admin:authentication_user_change", args=[self.admin_user.pk])

        self.assertEqual(self.client.get(url).status_code, 200)

    def test_add_form_stores_the_email_lowercased(self) -> None:
        response = self.client.post(
            reverse("admin:authentication_user_add"),
            {
                "email": "Ada@Example.com",
                "password1": "a-long-Pass-word-9",
                "password2": "a-long-Pass-word-9",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email="ada@example.com").exists())

    def test_add_form_refuses_an_email_that_differs_only_by_case(self) -> None:
        response = self.client.post(
            reverse("admin:authentication_user_add"),
            {
                "email": "ADMIN@example.com",
                "password1": "a-long-Pass-word-9",
                "password2": "a-long-Pass-word-9",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email__iexact="admin@example.com").count(), 1)
