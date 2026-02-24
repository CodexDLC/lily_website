from django.urls import path

from .views.appointments import appointments_view
from .views.appointments_new import appointments_new_view
from .views.contacts import contacts_view
from .views.reply import reply_form_view

app_name = "telegram_app"

urlpatterns = [
    path("reply/", reply_form_view, name="reply"),
    path("contacts/", contacts_view, name="contacts"),
    path("appointments/", appointments_view, name="appointments"),
    path("appointments_new/", appointments_new_view, name="appointments_new"),
]
