from django.contrib.auth.forms import BaseUserCreationForm

from authentication.models import User


class UserCreationForm(BaseUserCreationForm[User]):
    """The admin's "add user" form, asking for email and password (Django's asks for a username)."""

    class Meta:
        model = User
        fields = ("email",)
