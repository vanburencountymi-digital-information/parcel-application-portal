from django.conf import settings

from common.services import LoggingService


def config_warnings() -> list[str]:
    """Plain-English problems with the parcel settings that don't stop the app from starting
    but would make parcel lookup fail the first time someone uses it. Empty when all is well.
    """
    warnings = []
    if not settings.PARCEL_SERVICE_URL:
        warnings.append(
            "PARCEL_SERVICE_URL is not set, so parcel search and lookup will fail. "
            "Add it to .env (see .env.example)."
        )
    return warnings


def report_config_warnings() -> None:
    """Sends each config warning to Sentry. Called once at startup from `ParcelsConfig.ready()`.
    Nothing is sent when SENTRY_DSN is empty, as in local development and tests.
    """
    for warning in config_warnings():
        LoggingService().report_warning(f"Config warning: {warning}", tags={"app": "parcels"})
