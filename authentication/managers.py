from typing import TYPE_CHECKING, Any

from django.contrib.auth.base_user import BaseUserManager

if TYPE_CHECKING:
    from authentication.models import User


class UserManager(BaseUserManager["User"]):
    """Creates users that sign in with their email address (there is no username)."""

    @classmethod
    def normalize_email(cls, email: str | None) -> str:
        """The one place an email is cleaned up before it is stored or compared.

        Takes: email (str | None). Returns: it trimmed and fully lowercased ("" for None).
        Django's version lowercases only the domain; ours lowercases everything, because
        sign-in and django-guardian look users up by exact match and the database treats
        emails as the same ignoring case.
        """
        return (email or "").strip().lower()

    def create_user(self, email: str, password: str | None = None, **extra_fields: Any) -> User:
        """Creates and saves a user. The email is cleaned up by `normalize_email`.

        Takes: email (str), password (str | None; None makes it unusable, so the person
        signs in by emailed link), and any other user fields (e.g. `first_name`).
        Returns: the saved `User`.
        Raises: `ValueError` if the email is blank (or None).
        """
        email = self.normalize_email(email)
        if not email:
            raise ValueError("The email must be set.")
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email: str, password: str | None = None, **extra_fields: Any
    ) -> User:
        """Creates and saves a staff user who has every permission.

        Takes: email (str), password (str | None), and any other user fields. `is_staff` and
        `is_superuser` default to True and can be overridden here.
        Returns: the saved `User`.
        Raises: `ValueError` if the email is blank.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)
