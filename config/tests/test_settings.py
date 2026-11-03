from django.conf import settings
from django.test import SimpleTestCase


class RestFrameworkSettingsTests(SimpleTestCase):
    """DRF's defaults are open (anyone, no limits). These guard the safer ones we set."""

    def test_views_require_sign_in_by_default(self) -> None:
        self.assertEqual(
            settings.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"],
            ["rest_framework.permissions.IsAuthenticated"],
        )

    def test_views_are_rate_limited_by_default(self) -> None:
        self.assertEqual(
            settings.REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"],
            [
                "rest_framework.throttling.AnonRateThrottle",
                "rest_framework.throttling.UserRateThrottle",
            ],
        )
        self.assertEqual(set(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]), {"anon", "user"})

    def test_only_json_is_rendered_so_the_browsable_api_is_off(self) -> None:
        self.assertEqual(
            settings.REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"],
            ["rest_framework.renderers.JSONRenderer"],
        )
