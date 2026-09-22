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
        sentry_sdk.capture_exception(exc, tags=tags or {})
