"""Serializers for the parcel service's responses.

ParcelClient fetches JSON and hands it to these. Each one checks the shape, cleans up the
service's quirks, and `save()` returns our own types (`ParcelSearchResult`, `ParcelDetail`),
so the client has no parsing code of its own.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers
from rest_framework.fields import empty

from .types import ParcelDetail, ParcelSearchResult


class BlankIfMissingCharField(serializers.CharField):
    """Text the service may leave out or send as null. Both become "" instead of an error."""

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault("allow_blank", True)
        super().__init__(**kwargs)

    def run_validation(self, data: Any = empty) -> Any:
        """Takes: the raw value, which may be missing (`empty`) or None.
        Returns: "" for a missing or null value, otherwise the cleaned text.
        """
        if data is empty or data is None:
            return ""
        return super().run_validation(data)


class ZipCodeField(BlankIfMissingCharField):
    """A ZIP code as text, padded via to_internal_value back to five digits.

    Needed because the service sends some ZIPs (`owner_zip`) as JSON numbers, so a ZIP like
    02134 arrives as 2134. Anything that isn't all ASCII digits (such as "49064-1234") is left
    as is. DRF calls `to_internal_value` itself while validating; nothing in our code does.
    """

    def to_internal_value(self, data: Any) -> str:
        """Takes: a ZIP that is a string or a number. Returns: it as text, zero-padded to
        five digits when it is all ASCII digits.
        """
        value = super().to_internal_value(data)
        return value.zfill(5) if value.isascii() and value.isdigit() else value


class ParcelSearchRowSerializer(serializers.Serializer[Any]):
    """One row of search results."""

    id = serializers.IntegerField()
    parcel_no = serializers.CharField()
    address = BlankIfMissingCharField()
    # Search calls this `owner`; the detail response calls it `owner_name`. We use owner_name.
    # Likewise the service's `zip` is our `zip_code` (a bare `zip` is ambiguous).
    owner = BlankIfMissingCharField(source="owner_name")
    city = BlankIfMissingCharField()
    zip = ZipCodeField(source="zip_code")


class ParcelSearchResponseSerializer(serializers.Serializer[Any]):
    """The whole search response. `save()` returns a list of `ParcelSearchResult`."""

    results = ParcelSearchRowSerializer(many=True)

    def create(self, validated_data: dict[str, Any]) -> list[ParcelSearchResult]:
        """Takes: the validated response. Returns: one `ParcelSearchResult` per row."""
        return [ParcelSearchResult(**row) for row in validated_data["results"]]


class ParcelPropertiesSerializer(serializers.Serializer[Any]):
    """The `properties` of a parcel's GeoJSON Feature."""

    parcel_no = serializers.CharField()
    address = BlankIfMissingCharField()
    city = BlankIfMissingCharField()
    state = BlankIfMissingCharField()
    zip = ZipCodeField(source="zip_code")
    owner_name = BlankIfMissingCharField()
    owner_address = BlankIfMissingCharField()
    owner_city = BlankIfMissingCharField()
    owner_state = BlankIfMissingCharField()
    owner_zip = ZipCodeField(source="owner_zip_code")
    # Passed through as the service sends it. None when there's no acreage on record.
    acres = serializers.FloatField(allow_null=True, default=None)

    def get_fields(self) -> dict[str, Any]:
        """Returns: the declared fields plus `class`, which Python won't allow as an
        attribute name, stored as `property_class`.
        """
        fields = super().get_fields()
        fields["class"] = BlankIfMissingCharField(source="property_class")
        return fields


class ParcelDetailSerializer(serializers.Serializer[Any]):
    """A parcel as a GeoJSON Feature. `save()` returns a `ParcelDetail`.

    The response doesn't repeat the parcel's id, so it is a required argument:
    `ParcelDetailSerializer(data=payload, parcel_id=123)`.
    """

    properties = ParcelPropertiesSerializer()
    geometry = serializers.JSONField(allow_null=True, default=None)

    def __init__(self, *args: Any, parcel_id: int, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.parcel_id = parcel_id

    def create(self, validated_data: dict[str, Any]) -> ParcelDetail:
        """Takes: the validated response. Returns: the `ParcelDetail`, with the id we asked for."""
        return ParcelDetail(
            id=self.parcel_id,
            geometry=validated_data["geometry"],
            **validated_data["properties"],
        )
