from .client import ClientAdmin
from .email_content import EmailContentAdmin
from .seo import StaticPageSeoAdmin
from .settings import SiteSettingsAdmin
from .static import StaticTranslationAdmin
from .user_profile import UserProfileAdmin

__all__ = [
    "ClientAdmin",
    "EmailContentAdmin",
    "SiteSettingsAdmin",
    "StaticTranslationAdmin",
    "StaticPageSeoAdmin",
    "UserProfileAdmin",
]
