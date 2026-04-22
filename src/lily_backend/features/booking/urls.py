from django.urls import path

from .views import (
    AppointmentManageView,
    BookingCommitView,
    BookingSuccessGroupView,
    BookingSuccessMultiView,
    BookingSuccessSingleView,
    BookingWizardView,
    CancelAppointmentView,
    CancelSuccessView,
    CartAddView,
    CartRemoveView,
    CartSetModeView,
    CartSetStageView,
    ConfirmAppointmentView,
    RescheduleAppointmentView,
    SchedulerCalendarView,
    SchedulerConfirmTimeView,
    SchedulerSlotsItemView,
    SchedulerSlotsView,
)

app_name = "booking"

urlpatterns = [
    # ── Public booking wizard ──────────────────────────────────────────────────
    path("booking/", BookingWizardView.as_view(), name="booking_wizard"),
    # HTMX: Cart
    path("booking/cart/add/", CartAddView.as_view(), name="cart_add"),
    path("booking/cart/remove/", CartRemoveView.as_view(), name="cart_remove"),
    path("booking/cart/set-mode/", CartSetModeView.as_view(), name="cart_set_mode"),
    path("booking/cart/set-stage/", CartSetStageView.as_view(), name="cart_set_stage"),
    # HTMX: Scheduler
    path("booking/scheduler/calendar/", SchedulerCalendarView.as_view(), name="scheduler_calendar"),
    path("booking/scheduler/slots/", SchedulerSlotsView.as_view(), name="scheduler_slots"),
    path("booking/scheduler/slots/item/", SchedulerSlotsItemView.as_view(), name="scheduler_slots_item"),
    path("booking/scheduler/confirm-time/", SchedulerConfirmTimeView.as_view(), name="scheduler_confirm_time"),
    # Commit
    path("booking/commit/", BookingCommitView.as_view(), name="commit"),
    # ── Success pages ──────────────────────────────────────────────────────────
    path("booking/success/<str:token>/", BookingSuccessSingleView.as_view(), name="success_single"),
    path("booking/success/group/<str:token>/", BookingSuccessGroupView.as_view(), name="success_group"),
    path("booking/success/multi/", BookingSuccessMultiView.as_view(), name="success_multi"),
    # ── Appointment management (email token actions) ───────────────────────────
    path("appointments/manage/<str:token>/", AppointmentManageView.as_view(), name="booking_manage"),
    path("appointments/confirm/<str:token>/", ConfirmAppointmentView.as_view(), name="booking_confirm"),
    path("appointments/cancel/success/", CancelSuccessView.as_view(), name="cancel_success"),
    path("appointments/cancel/<str:token>/", CancelAppointmentView.as_view(), name="booking_cancel"),
    path("appointments/cancel/<str:token>/action/", CancelAppointmentView.as_view(), name="booking_cancel_action"),
    path("appointments/reschedule/<str:token>/", RescheduleAppointmentView.as_view(), name="booking_reschedule"),
]
