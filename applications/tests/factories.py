from factory import Sequence
from factory.django import DjangoModelFactory

from applications.models import AssessingUnit


class AssessingUnitFactory(DjangoModelFactory[AssessingUnit]):
    """A saved `AssessingUnit`. Defaults to a township with a unique name and no unit code."""

    class Meta:
        model = AssessingUnit

    name = Sequence(lambda n: f"Unit {n}")
    kind = AssessingUnit.Kind.TOWNSHIP
    parcel_unit_code = None
