from django.conf import settings
from django.db import IntegrityError, transaction
from django.test import TestCase
from guardian.utils import get_anonymous_user
from parameterized import parameterized

from authentication.models import User


class UserManagerTests(TestCase):
    def test_create_user_lowercases_and_trims_the_email(self) -> None:
        user = User.objects.create_user("  Ada@Example.COM ", password=None)

        self.assertEqual(user.email, "ada@example.com")

    def test_saving_any_way_lowercases_and_trims_the_email(self) -> None:
        user = User.objects.create(email="  Ada@Example.COM ")

        self.assertEqual(user.email, "ada@example.com")

    def test_create_user_without_a_password_has_an_unusable_one(self) -> None:
        self.assertFalse(User.objects.create_user("ada@example.com").has_usable_password())

    @parameterized.expand([("empty", ""), ("spaces", "   "), ("none", None)])
    def test_create_user_requires_an_email(self, _name: str, given: str | None) -> None:
        with self.assertRaisesMessage(ValueError, "email must be set"):
            User.objects.create_user(given)  # type: ignore[arg-type]  # None is the case under test

    def test_create_superuser_is_staff_and_superuser(self) -> None:
        user = User.objects.create_superuser("admin@example.com", password="x")

        self.assertTrue(user.is_staff and user.is_superuser)


class UserTests(TestCase):
    def test_email_is_unique_ignoring_case(self) -> None:
        User.objects.create_user("ada@example.com")

        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create(email="ADA@example.com")

    def test_blank_email_is_refused_even_without_the_manager(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create(email="   ")

    def test_str_is_the_email(self) -> None:
        self.assertEqual(str(User(email="ada@example.com")), "ada@example.com")


class GuardianAnonymousUserTests(TestCase):
    def test_anonymous_name_is_already_normalized(self) -> None:
        name = settings.ANONYMOUS_USER_NAME

        self.assertEqual(name, User.objects.normalize_email(name))

    def test_guardian_finds_its_anonymous_user(self) -> None:
        self.assertEqual(get_anonymous_user().email, settings.ANONYMOUS_USER_NAME)
