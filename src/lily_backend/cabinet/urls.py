from django.conf import settings
from django.urls import include, path

from .views.analytics import AnalyticsReportsView, analytics_dashboard_view
from .views.booking import (
    BookingActionView,
    BookingCreateView,
    BookingDayFetchView,
    BookingGroupActionView,
    BookingGroupListView,
    BookingListView,
    BookingModalView,
    BookingScheduleView,
    BookingSettingsView,
    BookingSlotFetchView,
    NewBookingView,
)
from .views.client import (
    ClientAppointmentsView,
    ClientCancelAppointmentView,
    ClientHomeView,
    ClientManageAppointmentView,
    ClientRescheduleConfirmView,
    ClientRescheduleModalView,
    ClientRescheduleSlotsView,
    ClientSettingsView,
)
from .views.conversations import (
    AllMessagesView,
    ComposeView,
    ImportedMailView,
    InboxBulkActionView,
    InboxView,
    ProcessedView,
    ThreadActionView,
    ThreadReplyActionView,
    ThreadView,
    manual_check_view,
)
from .views.ops import DataMaintenanceView, WorkerOpsView
from .views.services import CategoryStatusToggleView, ServiceQuickEditView, ServicesListView
from .views.site_settings import site_settings_tab_view, site_settings_view
from .views.staff import StaffListView, StaffQuickEditView
from .views.users import ClientDetailView, UserListView

app_name = "cabinet"

urlpatterns = [
    path("site/settings/", site_settings_view, name="site_settings"),
    path("site/settings/<str:tab_slug>/", site_settings_tab_view, name="site_settings_tab"),
    # Codex cabinet library: dashboard + generic routes
    path("", include("codex_django.cabinet.urls")),
    path("", include("cabinet.auth_urls")),
    path("my/", ClientHomeView.as_view(), name="client_home"),
    path("my/appointments/", ClientAppointmentsView.as_view(), name="client_appointments"),
    path(
        "my/appointments/manage/<str:token>/", ClientManageAppointmentView.as_view(), name="client_manage_appointment"
    ),
    path(
        "my/appointments/cancel/<str:token>/", ClientCancelAppointmentView.as_view(), name="client_cancel_appointment"
    ),
    path(
        "my/appointments/reschedule/<str:token>/", ClientRescheduleModalView.as_view(), name="client_reschedule_modal"
    ),
    path(
        "my/appointments/reschedule/<str:token>/slots/",
        ClientRescheduleSlotsView.as_view(),
        name="client_reschedule_slots",
    ),
    path(
        "my/appointments/reschedule/<str:token>/confirm/",
        ClientRescheduleConfirmView.as_view(),
        name="client_reschedule_confirm",
    ),
    path("my/settings/", ClientSettingsView.as_view(), name="settings"),
    # Analytics
    path("analytics/", analytics_dashboard_view, name="analytics_dashboard"),
    path("analytics/reports/", AnalyticsReportsView.as_view(), name="analytics_reports"),
    # Ops
    path("ops/workers/", WorkerOpsView.as_view(), name="ops_workers"),
    path("ops/maintenance/", DataMaintenanceView.as_view(), name="ops_maintenance"),
    # Booking
    path("booking/schedule/", BookingScheduleView.as_view(), name="booking_schedule"),
    path("booking/settings/", BookingSettingsView.as_view(), name="booking_settings"),
    path("booking/new/", NewBookingView.as_view(), name="booking_new"),
    path("booking/new/create/", BookingCreateView.as_view(), name="booking_create"),
    path("booking/appointments/", BookingListView.as_view(), name="booking_list"),
    path("booking/appointments/<str:status>/", BookingListView.as_view(), name="booking_list_filtered"),
    path("booking/<int:pk>/modal/", BookingModalView.as_view(), name="booking_modal"),
    path("booking/<int:pk>/action/<str:action>/", BookingActionView.as_view(), name="booking_action"),
    path("booking/groups/", BookingGroupListView.as_view(), name="booking_groups"),
    path("booking/groups/<int:pk>/action/<str:action>/", BookingGroupActionView.as_view(), name="booking_group_action"),
    path("booking/fetch-days/", BookingDayFetchView.as_view(), name="booking_fetch_days"),
    path("booking/fetch-slots/", BookingSlotFetchView.as_view(), name="booking_fetch_slots"),
    # Conversations
    path("conversations/", InboxView.as_view(), name="conversations_inbox"),
    path("conversations/imported/", ImportedMailView.as_view(), name="conversations_imported"),
    path("conversations/processed/", ProcessedView.as_view(), name="conversations_processed"),
    path("conversations/all/", AllMessagesView.as_view(), name="conversations_all"),
    path("conversations/compose/", ComposeView.as_view(), name="conversations_compose"),
    path("conversations/<int:pk>/", ThreadView.as_view(), name="conversations_thread"),
    path("conversations/<int:pk>/reply/", ThreadReplyActionView.as_view(), name="conversations_reply"),
    path("conversations/<int:pk>/action/<str:action>/", ThreadActionView.as_view(), name="conversations_action"),
    path("conversations/actions/bulk/", InboxBulkActionView.as_view(), name="conversations_bulk_action"),
    path("conversations/check-inbox/", manual_check_view, name="conversations_check_inbox"),
    # Users / Clients
    path("users/", UserListView.as_view(), name="users_list"),
    path("users/modal/<str:id_token>/", ClientDetailView.as_view(), name="user_modal"),
    path("users/<str:id_token>/modal/", ClientDetailView.as_view(), name="user_modal_legacy"),
    path("clients/ghost/<int:pk>/modal/", ClientDetailView.as_view(), name="client_ghost_modal"),
    # Staff / Masters
    path("staff/", StaffListView.as_view(), name="staff_list"),
    path("staff/modal/<int:pk>/", StaffQuickEditView.as_view(), name="staff_modal"),
    # Services catalog management
    path("services/", ServicesListView.as_view(), name="services_list"),
    path("services/<slug:category_slug>/", ServicesListView.as_view(), name="services_category"),
    path("services/<int:pk>/quick-edit/", ServiceQuickEditView.as_view(), name="service_quick_edit"),
    path("services/category/<int:pk>/toggle/", CategoryStatusToggleView.as_view(), name="service_category_toggle"),
    path("services/g/<str:group>/", ServicesListView.as_view(), name="services_group"),
]

if getattr(settings, "CODEX_ALLAUTH_ENABLED", False):
    urlpatterns.insert(2, path("", include("allauth.urls")))
