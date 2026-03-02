"""Price adjustment entry point for Administrators (QR flow)."""

from core.logger import log
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _
from django.views.generic import DetailView
from features.booking.models.appointment import Appointment
from features.booking.services.qr_service import AppointmentQRService
from features.cabinet.mixins import AdminRequiredMixin


class AppointmentPriceEditView(AdminRequiredMixin, DetailView):
    """
    View accessed by Admins scanning a QR code linked to a finalize_token.
    Allows changing the actual_price without altering the status.
    """

    model = Appointment
    template_name = "cabinet/appointments/edit_price.html"
    context_object_name = "appointment"
    slug_field = "finalize_token"
    slug_url_kwarg = "token"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        apt = self.object
        log.info(
            f"View: AppointmentPriceEdit | Action: GetContext | appointment_id={apt.id} | user={self.request.user.id}"
        )

        price = float(apt.price_actual if apt.price_actual is not None else (apt.price or 0.0))

        ctx["current_price"] = price
        ctx["price_suggestions"] = [
            price,
            price + 10,
            price + 20,
        ]
        # Add branded QR code for the admin to confirm/share
        ctx["qr_code_base64"] = AppointmentQRService.get_qr_base64(apt)
        return ctx

    def post(self, request, *args, **kwargs):
        appointment = self.get_object()

        # Security: already covered by AdminRequiredMixin, but we can double check
        if not request.user.is_staff:
            log.warning(f"View: AppointmentPriceEdit | Action: PostDenied | user={request.user.id}")
            raise PermissionDenied(_("Only administrators can adjust actual prices."))

        raw_price = request.POST.get("price_actual", "").strip()

        try:
            if not raw_price:
                raise ValueError(_("Price cannot be empty."))

            new_price = float(raw_price.replace(",", "."))
            if new_price < 0:
                raise ValueError(_("Price cannot be negative."))

            appointment.price_actual = new_price
            appointment.save(update_fields=["price_actual", "updated_at"])

            log.info(
                f"View: AppointmentPriceEdit | Action: PriceUpdated | "
                f"appointment_id={appointment.id} | new_price={new_price} | admin={request.user.id}"
            )

            messages.success(request, _("Actual price was successfully updated to € %(price)s.") % {"price": new_price})

        except ValueError as e:
            msg = str(e)
            if "could not convert" in msg:
                msg = _("Invalid price format. Please enter a valid number.")
            messages.error(request, msg)
            log.error(f"View: AppointmentPriceEdit | Action: PostFailed | error={msg}")

        # Redirect back to the same page or to appointments list
        # Depending on whether this was opened as a standalone tab from QR
        return HttpResponseRedirect(request.path)
