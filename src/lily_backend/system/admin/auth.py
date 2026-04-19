import contextlib

from allauth.account.admin import EmailAddressAdmin as BaseEmailAddressAdmin
from allauth.account.models import EmailAddress
from allauth.socialaccount.admin import SocialAccountAdmin as BaseSocialAccountAdmin
from allauth.socialaccount.admin import SocialAppAdmin as BaseSocialAppAdmin
from allauth.socialaccount.admin import SocialTokenAdmin as BaseSocialTokenAdmin
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin

with contextlib.suppress(admin.sites.NotRegistered):
    admin.site.unregister(Group)

with contextlib.suppress(admin.sites.NotRegistered):
    admin.site.unregister(EmailAddress)

with contextlib.suppress(admin.sites.NotRegistered):
    admin.site.unregister(SocialAccount)

with contextlib.suppress(admin.sites.NotRegistered):
    admin.site.unregister(SocialApp)

with contextlib.suppress(admin.sites.NotRegistered):
    admin.site.unregister(SocialToken)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


@admin.register(EmailAddress)
class EmailAddressAdmin(BaseEmailAddressAdmin, ModelAdmin):
    pass


@admin.register(SocialAccount)
class SocialAccountAdmin(BaseSocialAccountAdmin, ModelAdmin):
    pass


@admin.register(SocialApp)
class SocialAppAdmin(BaseSocialAppAdmin, ModelAdmin):
    pass


@admin.register(SocialToken)
class SocialTokenAdmin(BaseSocialTokenAdmin, ModelAdmin):
    pass
