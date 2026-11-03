from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from parcels.startup_warnings import config_warnings, report_config_warnings


class ConfigWarningsTests(SimpleTestCase):
    @override_settings(PARCEL_SERVICE_URL="https://parcels.example.test")
    def test_no_warnings_when_the_url_is_set(self) -> None:
        self.assertEqual(config_warnings(), [])

    @override_settings(PARCEL_SERVICE_URL="")
    def test_warns_when_the_url_is_missing(self) -> None:
        warnings = config_warnings()

        self.assertEqual(len(warnings), 1)
        self.assertIn("PARCEL_SERVICE_URL", warnings[0])


@patch("parcels.startup_warnings.LoggingService", autospec=True, spec_set=True)
class ReportConfigWarningsTests(SimpleTestCase):
    @override_settings(PARCEL_SERVICE_URL="")
    def test_reports_each_warning_to_sentry(self, mock_logging: MagicMock) -> None:
        report_config_warnings()

        mock_logging.return_value.report_warning.assert_called_once()
        args, kwargs = mock_logging.return_value.report_warning.call_args
        self.assertIn("PARCEL_SERVICE_URL", args[0])
        self.assertEqual(kwargs, {"tags": {"app": "parcels"}})

    @override_settings(PARCEL_SERVICE_URL="https://parcels.example.test")
    def test_reports_nothing_when_the_config_is_fine(self, mock_logging: MagicMock) -> None:
        report_config_warnings()

        mock_logging.return_value.report_warning.assert_not_called()
