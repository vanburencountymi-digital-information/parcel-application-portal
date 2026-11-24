from django.contrib.auth.hashers import make_password
from factory import Sequence
from factory.django import DjangoModelFactory

from authentication.models import User


class UserFactory(DjangoModelFactory[User]):
    """A saved user with a unique email and an unusable password."""

    class Meta:
        model = User

    email = Sequence(lambda n: f"user{n}@example.com")
    first_name = "Test"
    last_name = "Assessor"
    # Django treats a password starting with "!" as unusable (no one can sign in with it).
    password = make_password(None)
