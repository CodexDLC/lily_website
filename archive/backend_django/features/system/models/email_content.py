from codex_tools.notifications.adapters.mixins_django import BaseEmailContentMixin
from django.utils.translation import gettext_lazy as _


class EmailContent(BaseEmailContentMixin):
    """
    Project-specific implementation using library mixin.
    """

    class Meta(BaseEmailContentMixin.Meta):
        verbose_name = _("Email Content Block")
        verbose_name_plural = _("Email Content Blocks")
