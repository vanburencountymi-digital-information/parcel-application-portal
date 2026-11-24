from collections.abc import Iterable
from typing import Any

from factory import Sequence, SubFactory, Trait, post_generation
from factory.django import DjangoModelFactory

from applications.models import AssessingUnit, Assessor
from common.tests.factories import UserFactory


class AssessingUnitFactory(DjangoModelFactory[AssessingUnit]):
    """A saved `AssessingUnit`. Defaults to a township with a unique name and no unit code."""

    class Meta:
        model = AssessingUnit

    name = Sequence(lambda n: f"Unit {n}")
    kind = AssessingUnit.Kind.TOWNSHIP
    parcel_unit_code = None


class AssessorFactory(DjangoModelFactory[Assessor]):
    """A saved, active `Assessor` with its own user and no units by default.

    Takes: `assessing_units=[...]` (units or pks) to link existing units, or `with_unit=True`
    to create and link one new `AssessingUnit`. Both can be combined.
    """

    class Meta:
        model = Assessor

    user = SubFactory(UserFactory)
    is_active = True

    class Params:
        with_unit = Trait(assessing_units__with_unit=True)

    @post_generation
    def assessing_units(
        self, create: bool, extracted: Iterable[AssessingUnit | int] | None, **kwargs: Any
    ) -> None:
        """Links units after the assessor is saved (many-to-many needs a saved row).

        Takes: units or their pks via `assessing_units=[...]`, or `with_unit=True` for a new one.
        """
        if not create:
            return
        units = list(extracted or [])
        if kwargs.get("with_unit"):
            units.append(AssessingUnitFactory.create())
        if units:
            self.assessing_units.add(*units)
