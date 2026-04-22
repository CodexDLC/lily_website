# ═══════════════════════════════════════════
# Middleware definition
# ═══════════════════════════════════════════

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    # Page view tracking → Redis counters, zero DB load
    "features.main.middleware.CabinetRefreshMiddleware",
    "codex_django.tracking.middleware.PageTrackingMiddleware",
]
