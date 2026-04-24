from django.urls import path

from .views import ops, recipients

urlpatterns = [
    # Ops
    path("log/", ops.log_view, name="log_view"),
    # Recipients
    path("recipients/add/", recipients.add_recipient, name="add_recipient"),
    path("recipients/<int:pk>/toggle/", recipients.toggle_recipient, name="toggle_recipient"),
    path("recipients/<int:pk>/delete/", recipients.delete_recipient, name="delete_recipient"),
]
