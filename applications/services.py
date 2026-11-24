from collections.abc import Iterable

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db import IntegrityError, transaction

from applications.exceptions import AssessorValidationError
from applications.models import AssessingUnit, Assessor
from authentication.models import User


class AssessorService:
    """Creates assessors. This is the one place an assessor and their user are made together."""

    def create(
        self,
        email: str,
        assessing_units: Iterable[AssessingUnit],
        first_name: str = "",
        last_name: str = "",
        phone_number: str = "",
        is_active: bool = True,
    ) -> Assessor:
        """Creates a user and an `Assessor` for them, both or neither.

        Takes:
            email (str): the login, trimmed and lowercased.
            assessing_units (Iterable[AssessingUnit]): the units they work in.
            first_name (str): optional.
            last_name (str): optional.
            phone_number (str): optional; US numbers need no country code.
            is_active (bool): whether they can sign in as an assessor. Default True.
        Returns: the saved `Assessor` (Assessor). The user has no usable password: they
        sign in with an emailed link.
        Raises: `AssessorValidationError` if the user or assessor fails the model's own
        checks (bad or taken email, bad phone number). Nothing is saved then. Any other
        database error is raised unchanged.
        """
        user = User(
            email=User.objects.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
        )
        user.set_unusable_password()  # they sign in by emailed link
        assessor = Assessor(phone_number=phone_number, is_active=is_active)
        try:
            user.full_clean()
            assessor.full_clean(exclude=["user"])  # the user is linked once it is saved
        except ValidationError as error:
            raise AssessorValidationError(self._describe(error)) from error
        try:
            with transaction.atomic():
                user.save()
                assessor.user = user
                assessor.save()
                assessor.assessing_units.set(assessing_units)
        except IntegrityError as error:
            # Two creates at once can both pass the checks above. If the email is now
            # taken, that was the clash; anything else is a real bug, so let it through.
            if User.objects.filter(email__iexact=user.email).exists():
                raise AssessorValidationError(self._duplicate_email_message(user.email)) from error
            raise
        return assessor

    def _describe(self, error: ValidationError) -> str:
        """Takes: a `ValidationError` from `full_clean`. Returns: its problems as one readable line.

        `full_clean` always gives a dict of field -> messages. Each message is prefixed with its
        field name ("email: ...") so it makes sense on its own; errors that belong to no
        particular field are left unprefixed.
        """
        return " ".join(
            message if field == NON_FIELD_ERRORS else f"{field}: {message}"
            for field, messages in error.message_dict.items()
            for message in messages
        )

    def _duplicate_email_message(self, email: str) -> str:
        """Takes: the email (str). Returns: the message (str) shown when a user already has it."""
        return f"A user with the email {email} already exists."
