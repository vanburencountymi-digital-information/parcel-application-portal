from typing import Any, ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower

from authentication.managers import UserManager


class User(AbstractUser):
    """A person who can sign in. Identified by email; there is no username.

    Email is unique ignoring case, enforced by the database. Assessors and staff are
    both users; an assessor is a user with a linked `applications.Assessor`.
    """

    username = None  # type: ignore[assignment]  # removed: email is the identifier
    email = models.EmailField("email address", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    objects = UserManager()  # type: ignore[assignment,misc]  # replaces Django's username-based manager

    class Meta:
        ordering = ["email"]
        constraints = [
            # Lower() so "Ada@x.com" and "ada@x.com" count as the same user.
            models.UniqueConstraint(Lower("email"), name="unique_user_email_ignoring_case"),
            models.CheckConstraint(condition=~models.Q(email=""), name="user_email_not_blank"),
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Saves the user, first cleaning up the email with `UserManager.normalize_email`.

        Every way of saving a user (manager, admin, shell) stores the email the same way,
        so sign-in can match it exactly. The database constraints are the backstop: they
        refuse duplicates (ignoring case) and a blank email.

        Takes: `*args` and `**kwargs`, passed on to Django's `save` (Any).
        Returns: None.
        """
        self.email = type(self).objects.normalize_email(self.email)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """The email address."""
        return self.email
