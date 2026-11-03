# 0002. Use DRF serializers for the parcel service's responses

- **Status:** Accepted
- **Date:** 2026-11-03

## Context

Parcels come from the county parcel service (`ParcelClient`). Its JSON has quirks: the
owner is `owner` in search but `owner_name` in detail, some ZIPs arrive as numbers (losing
a leading zero), `class` is a Python keyword, and many fields can be missing or null. The
client first parsed all of this by hand, mixing fetching and parsing in one place.

## Decision

Add `djangorestframework` (and its mypy stubs) and parse every parcel service response
with serializers in `parcels/serializers.py`. The client only checks its inputs and
fetches; it hands the JSON to a serializer, and `save()` returns our own types
(`ParcelSearchResult`, `ParcelDetail`). A response that fails validation raises
`ParcelServiceError`.

## Alternatives considered

- **Hand-written parsing in the client**: what we had. Mixes two jobs and is harder to read and test.
- **Pydantic**: good typing, but a different style from `dice-document-pipeline-api`, which already uses DRF.
- **Django forms**: no new dependency, but built for user input and awkward for nested JSON.

## Consequences

- DRF is a new dependency, used here only for its serializers. There are no API views yet. `rest_framework` is in `INSTALLED_APPS`, and `REST_FRAMEWORK` sets safer defaults than DRF's own for any view added later: sign-in required, rate limited, JSON only.
- Quirks of the service live in one file, so changes to the service (such as the move to the authenticated endpoint) are made in the serializers.
- The same serializers are available if the portal later exposes its own API.
