import json
from typing import Any

from django.utils import timezone
from django_redis import get_redis_connection
from loguru import logger as log


class NotificationCacheManager:
    """
    Manager for seeding Redis caches from Django that the Telegram Bot consumes.
    Mirrors the key structure and JSON formatting expected by the Bot.
    """

    # Key patterns (must match src/telegram_bot/infrastructure/redis/managers/notifications/notification_keys.py)
    APPOINTMENT_CACHE_PREFIX = "notifications:cache:"
    GROUP_CACHE_PREFIX = "notifications:group_cache:"
    CONTACT_CACHE_PREFIX = "notifications:contact_cache:"

    TTL = 86400  # 24 hours

    @staticmethod
    def get_redis_client():
        return get_redis_connection("default")

    @classmethod
    def seed_appointment(cls, appointment_id: int, extra_data: dict[str, Any] | None = None) -> bool:
        """
        Fetches appointment data and saves a JSON snapshot to Redis.
        Used for single appointment notifications.
        """
        from django.utils import translation
        from features.booking.models.appointment import Appointment

        try:
            with translation.override("de"):
                appointment = Appointment.objects.select_related(
                    "client", "master", "service", "service__category", "active_promo"
                ).get(id=appointment_id)

                visits_count = Appointment.objects.filter(
                    client=appointment.client, status=Appointment.STATUS_COMPLETED
                ).count()

                # Convert UTC time from DB to local time (Europe/Berlin) before formatting
                local_dt = timezone.localtime(appointment.datetime_start)

                data = {
                    "id": appointment.id,
                    "client_name": f"{appointment.client.first_name} {appointment.client.last_name}",
                    "first_name": appointment.client.first_name,
                    "last_name": appointment.client.last_name,
                    "client_phone": appointment.client.phone or "",
                    "client_email": appointment.client.email or "",
                    "service_name": appointment.service.title,
                    "master_name": appointment.master.name,
                    "datetime": local_dt.strftime("%d.%m.%Y %H:%M"),
                    "duration_minutes": appointment.duration_minutes,
                    "price": float(appointment.price),
                    "request_call": False,
                    "client_notes": appointment.client_notes or "",
                    "visits_count": visits_count,
                    "category_slug": appointment.service.category.slug if appointment.service.category else None,
                    "active_promo_id": appointment.active_promo.id if appointment.active_promo else None,
                    "active_promo_title": appointment.active_promo.title if appointment.active_promo else None,
                }

            if extra_data:
                data.update(extra_data)

            key = f"{cls.APPOINTMENT_CACHE_PREFIX}{appointment_id}"
            cls.get_redis_client().set(key, json.dumps(data, ensure_ascii=False), ex=cls.TTL)
            log.info(f"Seeded appointment cache for ID={appointment_id} with local time: {data['datetime']}")
            return True

        except Exception as e:
            log.error(f"Failed to seed appointment cache for ID={appointment_id}: {e}")
            return False

    @classmethod
    def seed_group_appointment(cls, group_id: int, extra_data: dict[str, Any] | None = None) -> bool:
        """
        Fetches all appointments in a group and saves a unified JSON snapshot to Redis.
        Used for grouped notifications (one message for multiple services).
        """
        from django.utils import translation
        from features.booking.models.appointment_group import AppointmentGroup

        try:
            with translation.override("de"):
                group = AppointmentGroup.objects.select_related("client").get(id=group_id)
                items = group.items.select_related(
                    "appointment", "appointment__master", "appointment__service"
                ).order_by("order")

                if not items.exists():
                    log.warning(f"No items found for group ID={group_id}")
                    return False

                # Common client info
                data = {
                    "group_id": group.id,
                    "client_name": f"{group.client.first_name} {group.client.last_name}" if group.client else "Unknown",
                    "first_name": group.client.first_name if group.client else "",
                    "last_name": group.client.last_name if group.client else "",
                    "client_phone": group.client.phone if group.client else "",
                    "client_email": group.client.email if group.client else "",
                    "booking_date": group.booking_date.strftime("%d.%m.%Y"),
                    "total_price": float(sum(item.appointment.price for item in items)),
                    "total_duration": group.total_duration_minutes,
                    "notes": group.notes,
                    "items": [],
                }

                for item in items:
                    appt = item.appointment
                    local_dt = timezone.localtime(appt.datetime_start)
                    data["items"].append(
                        {
                            "appointment_id": appt.id,
                            "service_name": appt.service.title,
                            "master_name": appt.master.name,
                            "time": local_dt.strftime("%H:%M"),
                            "price": float(appt.price),
                            "duration": appt.duration_minutes,
                        }
                    )

            if extra_data:
                data.update(extra_data)

            key = f"{cls.GROUP_CACHE_PREFIX}{group_id}"
            cls.get_redis_client().set(key, json.dumps(data, ensure_ascii=False), ex=cls.TTL)
            log.info(f"Seeded group appointment cache for ID={group_id} with {len(data['items'])} items")
            return True

        except Exception as e:
            log.error(f"Failed to seed group appointment cache for ID={group_id}: {e}")
            return False

    @classmethod
    def seed_contact_request(cls, request_id: int, extra_data: dict[str, Any] | None = None) -> bool:
        """
        Fetches contact request data and saves a JSON snapshot to Redis.
        """
        from features.main.models.contact_request import ContactRequest

        try:
            request = ContactRequest.objects.select_related("client").get(id=request_id)

            # Convert UTC time from DB to local time (Europe/Berlin) before formatting
            local_created_at = timezone.localtime(request.created_at)

            data = {
                "request_id": request.id,
                "first_name": request.client.first_name,
                "last_name": request.client.last_name,
                "contact_value": request.client.phone or request.client.email or "n/a",
                "contact_type": "phone" if request.client.phone else "email",
                "topic": request.get_topic_display(),
                "message": request.message,
                "created_at": local_created_at.strftime("%d.%m.%Y %H:%M"),
            }

            if extra_data:
                data.update(extra_data)

            # Note: The Bot currently expects ContactNotificationPayload to have {request_id, text}
            data["text"] = data.get("message", "")

            key = f"{cls.CONTACT_CACHE_PREFIX}{request_id}"
            cls.get_redis_client().set(key, json.dumps(data, ensure_ascii=False), ex=cls.TTL)
            log.info(f"Seeded contact cache for ID={request_id} with local time: {data['created_at']}")
            return True

        except Exception as e:
            log.error(f"Failed to seed contact cache for ID={request_id}: {e}")
            return False
