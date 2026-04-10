from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from features.booking.dto.public_cart import SESSION_KEY, PublicCart, PublicCartItem


def _store_cart(client, *, service):
    session = client.session
    cart = PublicCart(
        items=[
            PublicCartItem(
                service_id=service.id,
                service_title=service.name,
                duration=service.duration,
                price=service.price,
            )
        ]
    )
    session[SESSION_KEY] = cart.to_dict()
    session.save()


def test_public_calendar_marks_available_days(client, service, master, booking_settings):
    service.masters.add(master)
    booking_settings.max_advance_days = 5
    booking_settings.save(update_fields=["max_advance_days"])
    _store_cart(client, service=service)

    response = client.get(reverse("booking:scheduler_calendar"))

    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert 'id="bk-calendar"' in content
    assert "bk-calendar__day" in content
    assert "available" in content


def test_public_slots_render_normalized_string_times(client, service, master):
    service.masters.add(master)
    _store_cart(client, service=service)
    target_date = timezone.localdate() + timedelta(days=1)

    response = client.get(
        reverse("booking:scheduler_slots"),
        {"date": target_date.isoformat()},
    )

    content = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "09:00" in content
    assert '"time": "09:00"' in content
