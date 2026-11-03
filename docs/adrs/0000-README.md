# Architecture Decision Records

- [0001. Use the Census Geocoder for address verification](0001-address-verification-census-geocoder.md) — Verify addresses with the free US Census Geocoder, since USPS's API terms only allow shipping/mailing use.
- [0002. Use DRF serializers for the parcel service's responses](0002-drf-serializers-for-parcel-service-responses.md) — Parse the parcel service's JSON with Django REST Framework serializers, so `ParcelClient` only fetches and the service's quirks live in one file.
