from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory
from django.urls import reverse

from src.lily_backend.cabinet.views.conversations import (
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


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def staff_user():
    user = MagicMock()
    user.is_active = True
    user.is_staff = True
    user.is_authenticated = True
    return user


@pytest.fixture
def mock_service():
    with patch("src.lily_backend.cabinet.views.conversations.ConversationsService") as mock:
        yield mock


def test_inbox_view(rf, staff_user, mock_service):
    url = reverse("cabinet:conversations_inbox")
    request = rf.get(url)
    request.user = staff_user

    mock_service.get_inbox_context.return_value = {"threads": []}

    view = InboxView.as_view()
    response = view(request)

    assert response.status_code == 200
    assert request.cabinet_module == "conversations"
    mock_service.get_inbox_context.assert_called_once()


def test_processed_view(rf, staff_user, mock_service):
    url = reverse("cabinet:conversations_processed")
    request = rf.get(url)
    request.user = staff_user

    view = ProcessedView.as_view()
    response = view(request)

    assert response.status_code == 200
    mock_service.get_inbox_context.assert_called_with(request, default_folder="processed")


def test_imported_mail_view(rf, staff_user, mock_service):
    url = reverse("cabinet:conversations_imported")
    request = rf.get(url)
    request.user = staff_user
    view = ImportedMailView.as_view()
    response = view(request)
    assert response.status_code == 200
    mock_service.get_inbox_context.assert_called_with(request, default_folder="email_import")


def test_all_messages_view(rf, staff_user, mock_service):
    url = reverse("cabinet:conversations_all")
    request = rf.get(url)
    request.user = staff_user
    view = AllMessagesView.as_view()
    response = view(request)
    assert response.status_code == 200
    mock_service.get_inbox_context.assert_called_with(request, default_folder="all")


def test_thread_view(rf, staff_user, mock_service):
    url = reverse("cabinet:conversations_thread", kwargs={"pk": 123})
    request = rf.get(url)
    request.user = staff_user

    mock_service.get_thread_context.return_value = {"thread": MagicMock()}

    view = ThreadView.as_view()
    response = view(request, pk=123)

    assert response.status_code == 200
    mock_service.get_thread_context.assert_called_with(pk=123)


def test_compose_post(rf, staff_user, mock_service):
    url = reverse("cabinet:conversations_compose")
    request = rf.post(url, data={"body": "test"})
    request.user = staff_user

    mock_service.compose_message.return_value = {"redirect_url": "/done/"}

    view = ComposeView.as_view()
    response = view(request)

    assert response.status_code == 302
    assert response.url == "/done/"


def test_thread_reply_post(rf, staff_user, mock_service):
    url = reverse("cabinet:conversations_reply", kwargs={"pk": 123})
    request = rf.post(url, data={"body": "reply"})
    request.user = staff_user

    mock_service.reply_to_thread.return_value = {"redirect_url": "/thread/123/"}

    view = ThreadReplyActionView.as_view()
    response = view(request, pk=123)

    assert response.status_code == 302
    mock_service.reply_to_thread.assert_called_with(pk=123, body="reply", user=staff_user)


def test_thread_action_view(rf, staff_user, mock_service):
    url = reverse("cabinet:conversations_action", kwargs={"pk": 123, "action": "archive"})
    request = rf.post(url)
    request.user = staff_user

    mock_service.perform_thread_action.return_value = {"redirect_url": "/inbox/"}

    view = ThreadActionView.as_view()
    response = view(request, pk=123, action="archive")

    assert response.status_code == 302
    mock_service.perform_thread_action.assert_called_with(pk=123, action="archive")


def test_inbox_bulk_action_view(rf, staff_user, mock_service):
    url = reverse("cabinet:conversations_bulk_action")
    request = rf.post(url, data={"thread_ids": "1,2", "action": "delete"})
    request.user = staff_user

    mock_service.perform_bulk_action.return_value = {"redirect_url": "/inbox/"}

    view = InboxBulkActionView.as_view()
    response = view(request)

    assert response.status_code == 302
    mock_service.perform_bulk_action.assert_called_with(request=request)


def test_manual_check_view(rf, staff_user, mock_service):
    url = reverse("cabinet:conversations_check_inbox")
    request = rf.post(url)
    request.user = staff_user

    mock_service.check_inbox.return_value = {"redirect_url": "/inbox/"}

    response = manual_check_view(request)

    assert response.status_code == 302
    assert response.url == "/inbox/"
