from . import auth
from .client import ClientAdmin
from .email_content import EmailContentAdmin
from .loyalty import LoyaltyProfileAdmin
from .seo import StaticPageSeoAdmin
from .settings import SiteSettingsAdmin
from .static import StaticTranslationAdmin
from .user_profile import UserProfileAdmin

__all__ = [
    "ClientAdmin",
    "EmailContentAdmin",
    "LoyaltyProfileAdmin",
    "SiteSettingsAdmin",
    "StaticTranslationAdmin",
    "StaticPageSeoAdmin",
    "UserProfileAdmin",
    "auth",
]
