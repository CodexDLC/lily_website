"""Shared fixtures for cabinet tests."""

import features.system.services.notification as notif_module
import pytest


@pytest.fixture(autouse=True)
def _reset_notification_engine():
    """Reset the NotificationService singleton between tests to prevent mock leaks."""
    notif_module._engine = None
    yield
    notif_module._engine = None
