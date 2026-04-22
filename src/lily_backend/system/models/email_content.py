from codex_django.notifications import BaseEmailContentMixin
from django.utils.translation import gettext_lazy as _


class EmailContent(BaseEmailContentMixin):
    """
    Stores editable email/notification content blocks with per-language text.
    Used by NotificationService to render localised email bodies and subjects.
    """

    class Meta(BaseEmailContentMixin.Meta):
        verbose_name = _("Email Content Block")
        verbose_name_plural = _("Email Content Blocks")
