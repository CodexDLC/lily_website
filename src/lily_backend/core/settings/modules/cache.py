import os
from pathlib import Path
from urllib.parse import quote_plus

# In container: /app. Locally: src/backend_django
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROJECT_NAME = BASE_DIR.name

# ═══════════════════════════════════════════
# Redis & ARQ
# ═══════════════════════════════════════════

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)

IS_INSIDE_DOCKER = os.path.exists("/.dockerenv")
if REDIS_HOST == "localhost" and IS_INSIDE_DOCKER:
    REDIS_HOST = "redis"

if REDIS_PASSWORD:
    clean_password = REDIS_PASSWORD.strip("'\"").strip()
    encoded_password = quote_plus(clean_password)
    REDIS_URL = f"redis://:{encoded_password}@{REDIS_HOST}:{REDIS_PORT}/0"
else:
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# ═══════════════════════════════════════════
# Cache & Sessions (Isolated by PROJECT_NAME)
# ═══════════════════════════════════════════

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "KEY_PREFIX": PROJECT_NAME,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_NAME = f"sessionid_{PROJECT_NAME}"

# --- Ratelimit ---
RATELIMIT_USE_CACHE = "default"
RATELIMIT_VIEW = "features.main.views.legal.ratelimit_view"
