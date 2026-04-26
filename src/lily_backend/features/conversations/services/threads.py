from typing import Any

from django.utils import timezone

from features.conversations.models import Message


def create_booking_thread(appt: Any) -> Message | None:
    """
    Create a conversation thread (Message) for a booking if it contains client notes.
    Allows staff to reply to the client's notes directly via the Conversations module.
    """
    client_notes = getattr(appt, "client_notes", "")
    if not client_notes:
        return None

    client = appt.client
    sender_name = client.first_name if client else ""
    sender_email = getattr(client, "email", "") if client else ""
    sender_phone = getattr(client, "phone", "") if client else ""

    service_name = appt.service.name if appt.service else "Service"
    subject = f"Booking Note: {service_name}"

    formatted_dt = timezone.localtime(appt.datetime_start).strftime("%d.%m.%Y %H:%M")
    body = f"Appointment: {formatted_dt}\nService: {service_name}\n\nNote:\n{client_notes}"

    msg = Message.objects.create(
        sender_name=sender_name or "Client",
        sender_email=sender_email,
        sender_phone=sender_phone,
        subject=subject,
        body=body,
        topic=Message.Topic.BOOKING,
        source=Message.Source.MANUAL,
    )
    return msg
