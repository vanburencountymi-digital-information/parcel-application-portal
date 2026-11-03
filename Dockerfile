# parcel-application-portal — dev image
#
# Run via docker-compose (app + Postgres — see docker-compose.yml):
#   docker compose up --build
#
# Run this image alone, no Postgres (falls back to sqlite per config/settings.py):
#   docker build -t parcel-application-portal .
#   docker run -p 8000:8000 --env-file .env parcel-application-portal

FROM python:3.14-alpine

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY manage.py .
COPY pyproject.toml .
COPY config/ ./config/
COPY templates/ ./templates/
COPY common/ ./common/
COPY addresses/ ./addresses/
COPY parcels/ ./parcels/
COPY documents/ ./documents/
COPY applications/ ./applications/

# ruff/mypy write cache dirs under /app when run via `docker compose run`, so
# it needs to be writable by the non-root user, not just root (the default
# owner of everything COPY'd above).
RUN addgroup -g 1000 app && adduser -D -u 1000 -G app app && chown -R app:app /app
USER app

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
