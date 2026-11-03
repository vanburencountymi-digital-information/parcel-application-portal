import sentry_sdk


class LoggingService:
    """Wraps whichever error-monitoring SDK is in use (Sentry) — the only place
    in the project that imports `sentry_sdk` directly, so swapping monitoring
    vendors, or adding a second one, never touches a calling app.

    Safe to call unconditionally: with SENTRY_DSN unset, sentry_sdk.init() (in
    config/settings.py) puts the SDK in no-op mode, so report_exception just
    does nothing rather than erroring.
    """

    def report_exception(self, exc: Exception, *, tags: dict[str, str] | None = None) -> None:
        """Sends an exception to Sentry.

        Takes: the exception, and optional tags to filter by in Sentry.
        Returns: nothing.
        """
        sentry_sdk.capture_exception(exc, tags=tags or {})

    def report_warning(self, message: str, *, tags: dict[str, str] | None = None) -> None:
        """Reports something worth noticing that isn't an exception, such as a missing
        setting found at startup. Shows up in Sentry at "warning" level.

        Takes: the message, and optional tags to filter by in Sentry.
        Returns: nothing.
        """
        sentry_sdk.capture_message(message, level="warning", tags=tags or {})
