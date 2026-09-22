# Parcel Application Portal

Django 6 project scaffold: Postgres, media via `django-storages` (S3-compatible —
local dev exercises this against [Garage](https://garagehq.deuxfleurs.fr/), prod
against a real S3-style bucket), `django-crispy-forms` + Bootstrap5 for forms, a
DB-backed background worker (`django-tasks`), object-level RBAC
(`django-guardian`), and a timestamped, reject/return-to-previous-step workflow
story (`django-fsm-2` + `django-fsm-log`) for the eventual application-review
process. No parcel/GIS table yet — the `addresses` app is just entry + USPS
verification of a free-text address.

## Getting started

```bash
cp .env.example .env
# fill in SECRET_KEY (see the comment in .env.example for how to generate one)
make init
```

`make init` builds the image, runs migrations, and starts `db` + `app` + `worker`
in the foreground. Visit http://localhost:8000/.

## Everyday commands

| Command | What it does |
| --- | --- |
| `make up` / `make down` | start / stop the stack |
| `make recreate` | stop, rebuild, and start again — use after editing `.env` (Docker only reads it at container creation) |
| `make migrate` | apply migrations |
| `make migrations` | run `makemigrations` inside the container, writing the new file back to your host (see the Makefile comment for why this target is different from the others) |
| `make shell` | a shell inside the `app` container |
| `make pyshell` | `manage.py shell` inside the `app` container |
| `make test` | run the test suite (`--settings=config.test_settings`) |
| `make garage` | pull + (re)start the local Garage container |

## Background tasks

Tasks run through [`django-tasks`](https://pypi.org/project/django-tasks/). By
default, `TASKS_BACKEND` is unset, so tasks run synchronously in-process
(`ImmediateBackend`) — no worker needed.

The DB-backed worker ([`django-tasks-db`](https://github.com/RealOrangeOne/django-tasks-db))
is installed and migrated, just not switched on yet. To use it: set
`TASKS_BACKEND=django_tasks_db.DatabaseBackend` in `.env`, `make recreate`, and
bring up the `worker` service (already defined in `docker-compose.yml`, running
`manage.py db_worker`, which polls the DB for new tasks) alongside `app`/`db`.

## Media storage (Garage)

By default, files are stored on local disk (`./media`). To instead exercise the
same storage backend a real S3-style bucket would in prod — an actual object
store, not local disk — bring up the bundled
[Garage](https://garagehq.deuxfleurs.fr/):

```bash
make garage
```

Garage is deliberately excluded from plain `make up`/`make recreate` (it's behind
a Compose profile) — `make garage` is the only thing that starts it, and it also
pulls the pinned image and force-recreates the container, so it's safe to re-run
any time you want a clean restart.

Garage needs its single-node "cluster" layout applied and a bucket + key created
once before it's usable — unlike a lot of S3-compatible tools this can't be a
single command, since Garage is built around a distributed-cluster model even
when you're only running one node. Run these once:

```bash
# Find your node's ID (a long hex string) — it has no role assigned yet.
docker compose exec garage /garage status

# Assign it a single-node layout and apply it (bump --version if this isn't the first apply).
docker compose exec garage /garage layout assign -z dc1 -c 1G <node ID from above>
docker compose exec garage /garage layout apply --version 1

# Create a bucket, a key, and grant the key access.
docker compose exec garage /garage bucket create parcel-application-portal-local
docker compose exec garage /garage key create parcel-application-portal-local-key
docker compose exec garage /garage bucket allow --read --write --owner parcel-application-portal-local --key parcel-application-portal-local-key

# Print the access key ID / secret access key you'll need below.
docker compose exec garage /garage key info parcel-application-portal-local-key --show-secret
```

> [!NOTE]
> These are the Garage v2.4.1 CLI commands per its own quick-start docs. If a
> command errors, check `docker compose exec garage /garage --help` (or the
> subcommand's own `--help`) — exact flags occasionally shift between Garage
> releases.

Then add the printed access/secret key to `.env` and `make recreate`:

```bash
S3_BUCKET_NAME=parcel-application-portal-local
S3_ENDPOINT_URL=http://garage:3900
S3_ACCESS_KEY=<printed above>
S3_SECRET_KEY=<printed above>
S3_REGION_NAME=garage
S3_ADDRESSING_STYLE=path
```

You can check if Garage is correctly hooked up, or if an object exists inside
of it, with `default_storage`:

```python
make pyshell
from django.core.files.storage import default_storage
default_storage.__class__  # Should be storages.backends.s3.S3Storage
default_storage.exists("some/key.txt")
```

## Address verification (USPS)

`addresses/services/usps.py` calls the current USPS Addresses API v3 (OAuth2 —
the old Web Tools XML API shut down January 2026). Set `USPS_CLIENT_ID` /
`USPS_CLIENT_SECRET` in `.env` (get these from https://developers.usps.com/)
for the `/address/` page to actually standardize what's entered; without them
the form still works but verification will fail with an inline error.
