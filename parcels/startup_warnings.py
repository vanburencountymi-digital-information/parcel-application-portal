from django.conf import settings

from common.services import LoggingService


def config_warnings() -> list[str]:
    """Plain-English problems with the parcel settings that don't stop the app from starting
    but would make parcel lookup fail the first time someone uses it.

    Takes: nothing (reads the parcel settings).
    Returns: one plain-English message per problem. Empty when all is well.
    """
    warnings = []
    if not settings.PARCEL_SERVICE_URL:
        warnings.append(
            "PARCEL_SERVICE_URL is not set, so parcel search and lookup will fail. "
            "Add it to .env (see .env.example)."
        )
    elif not settings.PARCEL_SERVICE_URL.lower().startswith("https://"):
        risk = (
            "the access token would be sent unencrypted"
            if settings.PARCEL_SERVICE_TOKEN
            else "parcel data could be read or changed on its way here"
        )
        warnings.append(f"PARCEL_SERVICE_URL doesn't start with https://, so {risk}.")
    return warnings


def report_config_warnings() -> None:
    """Sends each config warning to Sentry. Called once at startup from `ParcelsConfig.ready()`.
    Nothing is sent when SENTRY_DSN is empty, as in local development and tests.

    Takes: nothing. Returns: nothing.
    """
    for warning in config_warnings():
        LoggingService().report_warning(f"Config warning: {warning}", tags={"app": "parcels"})
