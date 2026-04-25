from django.urls import path

from ..views.booking import (
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

booking_urlpatterns = [
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
]
