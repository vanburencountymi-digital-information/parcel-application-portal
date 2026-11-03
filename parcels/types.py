from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ParcelSearchResult:
    """One row from the parcel service's search. No geometry."""

    id: int
    parcel_no: str
    address: str
    owner_name: str
    city: str
    zip_code: str


@dataclass(frozen=True)
class ParcelDetail:
    """A single parcel, as the parcel service describes it right now.

    Applications copy these fields (a snapshot), because the parcel service's data
    changes after an application is approved.
    """

    id: int
    parcel_no: str
    address: str
    city: str
    state: str
    zip_code: str
    owner_name: str
    owner_address: str
    owner_city: str
    owner_state: str
    owner_zip_code: str
    acres: float | None  # as the service sends it; None when it has no acreage on record
    property_class: str
    geometry: dict[str, Any] | None
