from django.conf import settings
from django.db import models
from django.db.models.functions import Lower
from phonenumber_field.modelfields import PhoneNumberField


class AssessingUnit(models.Model):
    """A township or city that assesses its own parcels. Assessors and applications belong to one.

    Villages are not listed: their parcels are assessed by the township they sit in.
    """

    class Kind(models.TextChoices):
        TOWNSHIP = "township", "Township"
        CITY = "city", "City"

    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    parcel_unit_code = models.CharField(max_length=10, null=True, blank=True, unique=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            # Lower() so "Lyons Township" and "lyons township" count as the same unit.
            models.UniqueConstraint(Lower("name"), "kind", name="unique_assessing_unit_name_kind"),
        ]

    def __str__(self) -> str:
        """Name and kind, e.g. "Lyons Township (Township)"."""
        return f"{self.name} ({self.get_kind_display()})"


class Assessor(models.Model):
    """A person who submits applications for the townships or cities they work in.

    Name and email live on the linked user. Create assessors with `AssessorService`.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="assessor"
    )
    assessing_units = models.ManyToManyField(AssessingUnit, related_name="assessors", blank=True)
    is_active = models.BooleanField(default=True)
    phone_number = PhoneNumberField(blank=True)

    class Meta:
        ordering = ["user__email"]

    def __str__(self) -> str:
        """Full name, or the email if no name is set."""
        return self.full_name or self.email

    @property
    def email(self) -> str:
        """The linked user's email. Read-only: change it on the user."""
        return self.user.email

    @property
    def first_name(self) -> str:
        """The linked user's first name."""
        return self.user.first_name

    @property
    def last_name(self) -> str:
        """The linked user's last name."""
        return self.user.last_name

    @property
    def full_name(self) -> str:
        """The linked user's first and last name, or "" if neither is set."""
        return self.user.get_full_name()
