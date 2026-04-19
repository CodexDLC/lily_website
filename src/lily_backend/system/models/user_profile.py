from typing import ClassVar

from codex_django.system.mixins import AbstractUserProfile
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserProfile(AbstractUserProfile):
    """
    Project-specific user profile.
    Holds personal account data obtained once the user is registered.
    """

    instagram = models.CharField(_("Instagram"), max_length=100, blank=True)
    telegram = models.CharField(_("Telegram"), max_length=100, blank=True)
    birth_date = models.DateField(_("Birth Date"), null=True, blank=True)

    # Privacy Settings
    show_avatar = models.BooleanField(_("Show Avatar"), default=True)
    show_birth_date = models.BooleanField(_("Show Birth Date"), default=True)
    show_visit_history = models.BooleanField(_("Show Visit History"), default=True)
    use_recommendations = models.BooleanField(_("Use Recommendations"), default=True)

    # Notification Settings
    notify_service = models.BooleanField(_("Service Notifications"), default=True)
    notify_reminders = models.BooleanField(_("Appointment Reminders"), default=True)

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"
        ordering: ClassVar[list[str]] = ["-created_at"]

    def __str__(self) -> str:
        return self.get_full_name() or f"Profile #{self.pk}"
