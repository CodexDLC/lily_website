import os
from pathlib import Path

from codex_django.core.i18n.discovery import discover_locale_paths

# Root of Django project: src/backend_django
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# ═══════════════════════════════════════════
# Internationalization
# ═══════════════════════════════════════════

LANGUAGE_CODE = os.environ.get("LANGUAGE_CODE", "en")
TIME_ZONE = os.environ.get("TIME_ZONE", "Europe/Berlin")
USE_I18N = True
USE_TZ = True
LANGUAGES = [
    ("en", "English"),
    ("de", "Deutsch"),
    ("ru", "Russian"),
    ("uk", "Ukrainian"),
]

import modeltranslation  # noqa

MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
MODELTRANSLATION_LANGUAGES = (
    "de",
    "en",
    "ru",
    "uk",
)
# Fallback chain: German is our absolute source of truth.
# If any translation is missing (RU, UK, or even EN), show the German version.
MODELTRANSLATION_FALLBACK_LANGUAGES = {
    "default": ("de",),
    "uk": ("de",),
    "ru": ("de",),
    "en": ("de",),
}

LOCALE_PATHS = discover_locale_paths(BASE_DIR)
