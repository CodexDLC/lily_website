import os
from pathlib import Path

# Root of Django project: src/backend_django
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROJECT_NAME = os.environ.get("PROJECT_NAME", "project_landing")

# ═══════════════════════════════════════════
# Static & Media
# ═══════════════════════════════════════════

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

# In Docker, static files are collected into a standard directory
IS_DOCKER = os.environ.get("IS_DOCKER", "False").lower() in ("true", "1", "t") or os.path.exists("/.dockerenv")

if IS_DOCKER:
    STATIC_ROOT = Path("/app/staticfiles")
    MEDIA_ROOT = Path("/app/media")
else:
    STATIC_ROOT = BASE_DIR / "staticfiles"
    MEDIA_ROOT = BASE_DIR / "media"

# We ignore source CSS files that are compiled into app.css
STATICFILES_IGNORE_PATTERNS = [
    "css/base/*",
    "css/site/*",
    "css/adaptive/*",
    "css/components/*",
    "css/cabinet/*",
    "css/admin/*",
    "css/pages/*",
    "css/base.css",
    "css/cabinet.css",
    "css/pwa.css",
]

MEDIA_URL = "/media/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
