from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from common.services import LoggingService


class LoggingServiceTests(SimpleTestCase):
    @patch("common.services.sentry_sdk.capture_exception", autospec=True)
    def test_report_exception_sends_the_exception_with_tags(self, mock_capture: MagicMock) -> None:
        error = ValueError("boom")

        LoggingService().report_exception(error, tags={"app": "parcels"})

        mock_capture.assert_called_once_with(error, tags={"app": "parcels"})

    @patch("common.services.sentry_sdk.capture_message", autospec=True)
    def test_report_warning_sends_a_warning_level_message(self, mock_capture: MagicMock) -> None:
        LoggingService().report_warning("Something is off", tags={"app": "parcels"})

        mock_capture.assert_called_once_with(
            "Something is off", level="warning", tags={"app": "parcels"}
        )

    @patch("common.services.sentry_sdk.capture_message", autospec=True)
    def test_report_warning_defaults_to_no_tags(self, mock_capture: MagicMock) -> None:
        LoggingService().report_warning("Something is off")

        mock_capture.assert_called_once_with("Something is off", level="warning", tags={})
