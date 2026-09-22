# 0001. Use the Census Geocoder for address verification

- **Status:** Accepted
- **Date:** 2026-09-22

## Context

`AddressService` verifies addresses through a pluggable client. The USPS Addresses
API can't be used: its terms only allow shipping/mailing use. There's no parcel/GIS
data yet to verify against.

## Decision

Use the [US Census Geocoder](https://geocoding.geo.census.gov/geocoder/)
(`CensusGeocoderClient`). It's free, keyless, and public domain, and it fits the
existing `standardize_address(...)` interface. Zero or multiple matches fail
verification.

## Alternatives considered

- **Smarty / Lob / Melissa / Loqate**: CASS-certified and closest to USPS results, but paid. Only worth it if deliverability matters.
- **Geocodio**: cheap, but a paid vendor for little gain over Census.
- **Google Address Validation**: terms restrict storing results.
- **Self-hosted (Pelias/Nominatim, libpostal)**: too much operational work for now.

## Consequences

- "Verified" means the house number falls in a real street segment's address range, not that USPS delivers there.
- `line2` (unit) isn't checked; ZIPs are 5-digit only.
- No SLA; outages show as a form error and the address is saved unverified.
- Revisit once parcel data exists: verify against county parcel/address data, with Census as a fallback.
