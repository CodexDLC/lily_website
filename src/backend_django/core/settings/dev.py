"""
lily_website — Development Settings.

Inherits from base.py. SQLite, DEBUG=True, verbose logging.
"""

from .base import *  # noqa: F401,F403

# ═══════════════════════════════════════════
# Debug
# ═══════════════════════════════════════════

DEBUG = True

INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa: F405
INTERNAL_IPS = ["127.0.0.1"]

# ═══════════════════════════════════════════
# CSRF Trusted Origins
# ═══════════════════════════════════════════

CSRF_TRUSTED_ORIGINS = ["http://localhost:8080"]

# ═══════════════════════════════════════════
# Database — SQLite
# ═══════════════════════════════════════════

# SQLite is already configured in base.py as default.
# No changes needed here unless you want to override.

# ═══════════════════════════════════════════
# Logging
# ═══════════════════════════════════════════

# In dev, we might want more verbose logging to console
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
}
