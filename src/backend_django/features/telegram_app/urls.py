from django.urls import path

from .views.reply import reply_form_view

app_name = "telegram_app"

urlpatterns = [
    path("reply/", reply_form_view, name="reply"),
]
