from factory import SelfAttribute, SubFactory
from factory.django import DjangoModelFactory

from applications.models import Application
from assessing.tests.factories import AssessingUnitFactory, AssessorFactory


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
