import os
from pathlib import Path

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
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
else:
    clean_password = None
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# ═══════════════════════════════════════════
# Cache & Sessions (Isolated by PROJECT_NAME)
# ═══════════════════════════════════════════

CACHES = {
    "default": {
        "BACKEND": "codex_django.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "KEY_PREFIX": PROJECT_NAME,
        "TIMEOUT": 300,
        "OPTIONS": {
            "PASSWORD": clean_password,
        },
    }
}

SESSION_ENGINE = "codex_django.sessions.backends.redis"
SESSION_COOKIE_NAME = f"sessionid_{PROJECT_NAME}"

# --- Ratelimit ---
RATELIMIT_USE_CACHE = "default"
RATELIMIT_VIEW = "features.main.views.legal.ratelimit_view"
