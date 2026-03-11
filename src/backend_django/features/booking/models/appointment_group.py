"""AppointmentGroup and AppointmentGroupItem models for V2 booking."""

from django.db import models
from django.utils.translation import gettext_lazy as _
from features.system.models.mixins import TimestampMixin


class AppointmentGroup(TimestampMixin, models.Model):
    """
    Группа связанных записей, созданных через V2 конструктор бронирования.
    """

    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, _("Pending")),
        (STATUS_CONFIRMED, _("Confirmed")),
        (STATUS_COMPLETED, _("Completed")),
        (STATUS_CANCELLED, _("Cancelled")),
    ]

    client = models.ForeignKey(
        "booking.Client",
        on_delete=models.SET_NULL,
        null=True,
        related_name="appointment_groups",
        verbose_name=_("Client"),
    )
    lang = models.CharField(
        max_length=10,
        default="de",
        verbose_name=_("Language"),
        help_text=_("Language used during booking"),
    )
    booking_date = models.DateField(
        verbose_name=_("Booking Date"),
        help_text=_("Primary date for the visit (all services for SINGLE_DAY mode)."),
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name=_("Status"),
    )
    engine_mode = models.CharField(
        max_length=30,
        default="single_day",
        verbose_name=_("Engine Mode"),
        help_text=_("BookingMode used when this group was created."),
    )
    total_duration_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total Duration (min)"),
    )
    notes = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Notes"),
    )

    class Meta:
        verbose_name = _("Appointment Group")
        verbose_name_plural = _("Appointment Groups")
        ordering = ["-booking_date", "-created_at"]

    def __str__(self) -> str:
        client_str = str(self.client) if self.client else "Unknown"
        return f"Group #{self.pk} | {client_str} | {self.booking_date}"

    def cancel_all(self) -> None:
        """
        Отменяет всю группу: статус группы и всех связанных Appointment.
        """
        from features.booking.models.appointment import Appointment

        self.status = self.STATUS_CANCELLED
        self.save(update_fields=["status", "updated_at"])

        appointment_ids = self.items.values_list("appointment_id", flat=True)
        Appointment.objects.filter(
            id__in=appointment_ids, status__in=[Appointment.STATUS_PENDING, Appointment.STATUS_CONFIRMED]
        ).update(status=Appointment.STATUS_CANCELLED, cancelled_at=self.updated_at)

    def complete_all(self) -> None:
        """
        Завершает всю группу: статус группы и всех связанных Appointment.
        """
        from features.booking.models.appointment import Appointment

        self.status = self.STATUS_COMPLETED
        self.save(update_fields=["status", "updated_at"])

        appointment_ids = self.items.values_list("appointment_id", flat=True)
        Appointment.objects.filter(id__in=appointment_ids, status=Appointment.STATUS_CONFIRMED).update(
            status=Appointment.STATUS_COMPLETED
        )

    def approve_all(self) -> None:
        """
        Подтверждает всю группу.
        """
        from features.booking.models.appointment import Appointment

        self.status = self.STATUS_CONFIRMED
        self.save(update_fields=["status", "updated_at"])

        appointment_ids = self.items.values_list("appointment_id", flat=True)
        Appointment.objects.filter(id__in=appointment_ids, status=Appointment.STATUS_PENDING).update(
            status=Appointment.STATUS_CONFIRMED
        )


class AppointmentGroupItem(models.Model):
    """
    Связь между AppointmentGroup и конкретным Appointment.
    """

    group = models.ForeignKey(
        AppointmentGroup,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Group"),
    )
    appointment = models.OneToOneField(
        "booking.Appointment",
        on_delete=models.CASCADE,
        related_name="group_item",
        verbose_name=_("Appointment"),
    )
    service = models.ForeignKey(
        "main.Service",
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",
        verbose_name=_("Service"),
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_("Order in Chain"),
        help_text=_("Position of this service in the booking chain (0-indexed)."),
    )

    class Meta:
        verbose_name = _("Appointment Group Item")
        verbose_name_plural = _("Appointment Group Items")
        ordering = ["order"]
        unique_together = [("group", "order")]

    def __str__(self) -> str:
        svc = str(self.service) if self.service else "?"
        return f"Item #{self.order}: {svc} -> Apt #{self.appointment_id}"
