import os

# ═══════════════════════════════════════════
# Authentication & django-allauth
# ═══════════════════════════════════════════

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_UNIQUE_EMAIL = True

LOGIN_URL = "/cabinet/login/"
LOGIN_REDIRECT_URL = "/cabinet/"
LOGOUT_REDIRECT_URL = "/cabinet/login/"

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
            "secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
        },
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}

# Cabinet adapter hooks are scaffold-owned now.
ACCOUNT_ADAPTER = "cabinet.adapters.CabinetAccountAdapter"
ACCOUNT_MESSAGES = False  # Disable allauth success messages to prevent UI clutter
CABINET_DEFAULT_URL = "/cabinet/"
CABINET_CLIENT_URL = "/cabinet/my/"

CODEX_CABINET_SITE_URL = "/"
CODEX_CABINET_CLIENT_URL_NAME = "cabinet:client_home"
CODEX_CABINET_STAFF_URL_NAME = "cabinet:dashboard"
CODEX_CABINET_LOGIN_URL_NAME = "account_login"
CODEX_CABINET_LOGIN_URL_NAME = "account_login"
CODEX_CABINET_LOGOUT_URL_NAME = "account_logout"

# ═══════════════════════════════════════════
# Tracking & Analytics
# ═══════════════════════════════════════════
CODEX_TRACKING = {
    "enabled": True,
    "redis_enabled": True,
    "track_anonymous": True,
    "track_redirects": True,
    "track_dashboard_widgets": False,
    "skip_prefixes": (
        "/api/",
        "/cabinet/",
        "/de/cabinet/",
        "/en/cabinet/",
        "/django-prometheus/",
        "/favicon",
        "/static/",
        "/media/",
    ),
}
