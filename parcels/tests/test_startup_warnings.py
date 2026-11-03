from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings
from parameterized import parameterized

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

    @parameterized.expand(
        [
            ("http_with_token", "http://parcels.example.test", "secret", "token"),
            ("http_without_token", "http://parcels.example.test", "", "read or changed"),
            ("no_scheme_with_token", "parcels.example.test", "secret", "token"),
        ]
    )
    def test_warns_when_the_url_is_not_https(
        self, _name: str, url: str, token: str, expected: str
    ) -> None:
        with override_settings(PARCEL_SERVICE_URL=url, PARCEL_SERVICE_TOKEN=token):
            warnings = config_warnings()

        self.assertEqual(len(warnings), 1)
        self.assertIn("https://", warnings[0])
        self.assertIn(expected, warnings[0])
        self.assertNotIn(token or "-", warnings[0])

    @parameterized.expand(
        [("lowercase", "https://parcels.example.test"), ("uppercase", "HTTPS://X")]
    )
    def test_no_warning_for_an_https_url(self, _name: str, url: str) -> None:
        with override_settings(PARCEL_SERVICE_URL=url, PARCEL_SERVICE_TOKEN="secret"):
            self.assertEqual(config_warnings(), [])

    @override_settings(PARCEL_SERVICE_URL="")
    def test_a_missing_url_gets_only_the_missing_warning(self) -> None:
        self.assertEqual(len(config_warnings()), 1)


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
