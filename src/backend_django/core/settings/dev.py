"""
lily_website — Development Settings.

Inherits from base.py. SQLite, DEBUG=True, verbose logging.
"""

from .base import *  # noqa: F401,F403

# ═══════════════════════════════════════════
# Development overrides
# ═══════════════════════════════════════════

DEBUG = True

# Logging Level for Dev
LOG_LEVEL_CONSOLE = "DEBUG"

# SQLite for dev (already default in base.py)
# Override DATABASE if needed:
# DATABASES["default"] = {
#     "ENGINE": "django.db.backends.sqlite3",
#     "NAME": BASE_DIR / "db.sqlite3",
# }

# ═══════════════════════════════════════════
# Debug tools (add django-debug-toolbar here)
# ═══════════════════════════════════════════

INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
INTERNAL_IPS = ["127.0.0.1"]
