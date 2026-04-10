from django.apps import AppConfig


class TrackingConfig(AppConfig):
    name = "tracking"
    label = "tracking"
    verbose_name = "Page Tracking"

    def ready(self) -> None:
        # Auto-register dashboard providers when cabinet is installed
        import contextlib

        with contextlib.suppress(Exception):
            from . import providers  # noqa: F401
