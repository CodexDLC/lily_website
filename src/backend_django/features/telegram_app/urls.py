from django.urls import path

from .views.contacts import contacts_view
from .views.reply import reply_form_view

app_name = "telegram_app"

urlpatterns = [
    path("reply/", reply_form_view, name="reply"),
    path("contacts/", contacts_view, name="contacts"),
]
