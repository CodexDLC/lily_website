import pytest
from django.urls import reverse
from system.models import Client


@pytest.mark.django_db
def test_unsubscribe_view_get(client):
    c = Client.objects.create(email="c1@example.com", consent_marketing=True)
    url = reverse("unsubscribe", kwargs={"token": str(c.unsubscribe_token)})
    response = client.get(url)
    assert response.status_code == 200
    assert b"unsubscribe" in response.content.lower()


@pytest.mark.django_db
def test_unsubscribe_view_get_not_found(client):
    import uuid

    url = reverse("unsubscribe", kwargs={"token": str(uuid.uuid4())})
    response = client.get(url)
    assert response.status_code == 200
    assert b"not found" in response.content.lower() or b"invalid" in response.content.lower()


@pytest.mark.django_db
def test_unsubscribe_view_post(client):
    c = Client.objects.create(email="c1@example.com", consent_marketing=True)
    url = reverse("unsubscribe", kwargs={"token": str(c.unsubscribe_token)})
    response = client.post(url)
    assert response.status_code == 200
    assert b"success" in response.content.lower()

    c.refresh_from_db()
    assert c.consent_marketing is False
    assert c.email_opt_out_at is not None
