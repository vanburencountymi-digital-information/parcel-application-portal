# CHANGELOG

<!-- version list -->

## v1.5.0 (2026-11-24)

### Chores

- Bump django-fsm-2 to 4.3.0 and django-fsm-log to 6.0.0
  ([`08eb6ae`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/08eb6aee4265abe41a3d08bc97b92fbf93ddce3d))

- Bump patch-level dependencies
  ([`2f2edd7`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/2f2edd7b247c003517efa324dbbf0e8a4c86b5b5))

- Bump ruff to 0.17.6 and mypy to 2.4.1
  ([`f8172ea`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/f8172eaf47803db25edd035db34ba3c6d3aa4b8b))

- Regenerate migrations for the assessing app
  ([`1eb2897`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/1eb28971b8940a97cd9605dd7c5f0f6b8d3e97e4))

### Features

- Add Application model with FSM status
  ([`6477cdd`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/6477cdd70833cb6d339e941fcdc421682c3682fd))

### Refactoring

- Move AssessingUnit and Assessor into a new assessing app
  ([`b8c27c7`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/b8c27c7901a1de2b71b50fc014bfc359269facdf))


## v1.4.0 (2026-11-24)

### Features

- Add Assessor admin
  ([`2d3fc94`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/2d3fc94933619ee132a8cbacda601b94543f6c50))

- Add Assessor model with factory and tests
  ([`590cf71`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/590cf7192f69b0f7e1811a9e20a36cf3d48d9791))

- Add Assessor name and email properties
  ([`38d6df0`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/38d6df077dd710c1d261deb49467ca7036e90ee4))

- Add AssessorService
  ([`13a90cf`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/13a90cf7e8f9befef7a80663d04914b13284ff00))

- Add authentication app with custom User model
  ([`f209746`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/f209746b11efca1a62e79118d9d8bb63f33e273e))

- Add django-phonenumber-field with US default region
  ([`9630154`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/963015451bdf837421f94918d2c9762c965811d2))


## v1.3.0 (2026-11-23)

### Chores

- Add factory_boy for test factories
  ([`d5c711f`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/d5c711ff73262557666b256b7185048d424d9a1b))

- Enable ruff D105 and S rules
  ([`fbf1c09`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/fbf1c099dc528015c9efa802a77e377cdcc0c0ca))

### Features

- Add AssessingUnit model
  ([`dd30e58`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/dd30e58d60500277843ed90aa9887c5e09b110e6))

### Testing

- Use factory_boy for documents tests
  ([`2f48731`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/2f48731bd71930d0272545e041005f65c490b028))


## v1.2.0 (2026-11-03)

### Bug Fixes

- Report warning if parcel client url not set
  ([`fc5ff8f`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/fc5ff8f8249dd2351bf30fff4ec8c263d9b8c842))

### Chores

- Scaffold parcels, documents, and applications apps
  ([`5fdefcf`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/5fdefcf3b8270c6bb0a279ad82582e5aee5acb69))

### Features

- Add Document model
  ([`850ccf2`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/850ccf2cb4e99c57b52319f52e1ad23bbcb28fde))

- Add DocumentService with upload validation and docstring lint rules
  ([`79fa9e4`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/79fa9e4906dba3ad507670882452e1519c01ab0f))

- Add ParcelClient with DRF serializers for the parcel service
  ([`a168352`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/a1683522ef2833362dd031a468425e7947265374))


## v1.1.0 (2026-09-22)

### Features

- Drop USPS for geocoder
  ([`def6b0b`](https://github.com/vanburencountymi-digital-information/parcel-application-portal/commit/def6b0b78426a3875c44d872198a631367ebba46))


## v1.0.0 (2026-09-22)

- Initial Release
