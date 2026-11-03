from django.apps import AppConfig


class ParcelsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "parcels"

    def ready(self) -> None:
        from parcels.startup_warnings import report_config_warnings

        report_config_warnings()
