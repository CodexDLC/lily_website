from django.urls import path

from ..views.conversations import (
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

conversations_urlpatterns = [
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
]
