from unittest.mock import AsyncMock, patch

import pytest
from django.urls import reverse
from features.conversations.models.campaign import Campaign
from system.models import Client


@pytest.fixture
def staff_client(client):
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    user = user_model.objects.create_user(username="staff", email="staff@example.com", password="password", is_staff=True)
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_campaign_list_view(staff_client):
    Campaign.objects.create(subject="Test 1", body_text="Body")
    url = reverse("cabinet:conversations_campaigns")
    response = staff_client.get(url)
    assert response.status_code == 200
    assert b"Test 1" in response.content


@pytest.mark.django_db
def test_campaign_create_view_draft(staff_client):
    url = reverse("cabinet:conversations_campaigns_new")
    data = {
        "subject": "New Campaign",
        "body_text": "Body text",
        "template_key": "basic",
        "action": "draft",
    }
    response = staff_client.post(url, data)
    assert response.status_code == 302
    assert Campaign.objects.filter(subject="New Campaign", status=Campaign.Status.DRAFT).exists()


@pytest.mark.django_db
def test_campaign_create_view_send(staff_client):
    # Mocking the service to avoid actual arq enqueue
    with patch(
        "features.conversations.services.campaign_service.CampaignService.send", new_callable=AsyncMock
    ) as mock_send:
        url = reverse("cabinet:conversations_campaigns_new")
        data = {
            "subject": "Send Campaign",
            "body_text": "Body text",
            "template_key": "basic",
            "action": "send",
        }
        response = staff_client.post(url, data)
        assert response.status_code == 302
        assert Campaign.objects.filter(subject="Send Campaign").exists()
        assert mock_send.called


@pytest.mark.django_db
def test_campaign_detail_view(staff_client):
    campaign = Campaign.objects.create(subject="Detail", body_text="Body")
    url = reverse("cabinet:conversations_campaigns_detail", kwargs={"pk": campaign.pk})
    response = staff_client.get(url)
    assert response.status_code == 200
    assert b"Detail" in response.content


@pytest.mark.django_db
def test_audience_count_view(staff_client):
    Client.objects.create(email="c1@example.com", consent_marketing=True)
    url = reverse("cabinet:conversations_campaigns_audience_count")
    response = staff_client.get(url)
    assert response.status_code == 200
    assert response.content.decode() == "1"
