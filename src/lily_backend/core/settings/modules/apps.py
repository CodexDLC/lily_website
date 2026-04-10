# ═══════════════════════════════════════════
# Application definition
# ═══════════════════════════════════════════

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
]

THIRD_PARTY_APPS = [
    # Auth
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    # Admin
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "unfold.contrib.import_export",
    "unfold.contrib.guardian",
    "unfold.contrib.simple_history",
    "django_prometheus",
    "ninja",
]

# ═══════════════════════════════════════════
# Codex Library Apps
# ═══════════════════════════════════════════
CODEX_APPS = [
    "codex_django.core",
    "codex_django.cabinet",
    "codex_django.showcase",
]

# ═══════════════════════════════════════════
# Codex Library Settings
# ═══════════════════════════════════════════
CODEX_SITE_SETTINGS_MODEL = "system.SiteSettings"
CODEX_STATIC_TRANSLATION_MODEL = "system.StaticTranslation"
CODEX_STATIC_PAGE_SEO_MODEL = "system.StaticPageSeo"

LOCAL_APPS = [
    "core",
    "system",
    "tracking",
    "features.main",
    "cabinet",
    "features.conversations",
    "features.booking",
]

INSTALLED_APPS = (
    ["modeltranslation", "cabinet"]
    + CODEX_APPS
    + THIRD_PARTY_APPS
    + DJANGO_APPS
    + [a for a in LOCAL_APPS if a != "cabinet"]
)
