from datetime import timedelta

from django.utils import timezone
from factory import LazyAttribute, LazyFunction, SelfAttribute, SubFactory, Trait
from factory.django import DjangoModelFactory

from applications.models import Application, ApplicationHold
from assessing.tests.factories import AssessingUnitFactory, AssessorFactory
from common.tests.factories import UserFactory


class ApplicationFactory(DjangoModelFactory[Application]):
    """A saved draft split with its own unit and assessor; the contact is the submitter.

    Takes: `status=` to start in another state (it can only be set when the row is created;
    without it the model default, draft, applies), or any other field.
    """

    class Meta:
        model = Application

    type = Application.Type.SPLIT
    assessing_unit = SubFactory(AssessingUnitFactory)
    submitted_by = SubFactory(AssessorFactory)
    contact = SelfAttribute("submitted_by")


class ApplicationHoldFactory(DjangoModelFactory[ApplicationHold]):
    """A saved open hold (delinquent taxes) on a new application, placed by a new user.

    Takes: `released=True` for a hold released an hour after it was placed (with a releasing
    user), or any other field. The application is not moved to `on_hold`; that is the
    service's job.
    """

    class Meta:
        model = ApplicationHold

    application = SubFactory(ApplicationFactory)
    kind = ApplicationHold.Kind.DELINQUENT_TAXES
    placed_by = SubFactory(UserFactory)
    placed_at = LazyFunction(timezone.now)

    class Params:
        released = Trait(
            released_by=SubFactory(UserFactory),
            released_at=LazyAttribute(lambda hold: hold.placed_at + timedelta(hours=1)),
        )
