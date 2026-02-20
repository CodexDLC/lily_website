import json
from typing import Any

from django_redis import get_redis_connection
from loguru import logger as log


class NotificationCacheManager:
    """
    Manager for seeding Redis caches from Django that the Telegram Bot consumes.
    Mirrors the key structure and JSON formatting expected by the Bot.
    """

    # Key patterns (must match src/telegram_bot/infrastructure/redis/managers/notifications/notification_keys.py)
    APPOINTMENT_CACHE_PREFIX = "notifications:cache:"
    CONTACT_CACHE_PREFIX = "notifications:contact_cache:"

    TTL = 86400  # 24 hours

    @staticmethod
    def get_redis_client():
        return get_redis_connection("default")

    @classmethod
    def seed_appointment(cls, appointment_id: int, extra_data: dict[str, Any] | None = None) -> bool:
        """
        Fetches appointment data and saves a JSON snapshot to Redis.
        """
        from features.booking.models.appointment import Appointment

        try:
            appointment = Appointment.objects.select_related(
                "client", "master", "service", "service__category", "active_promo"
            ).get(id=appointment_id)

            visits_count = Appointment.objects.filter(
                client=appointment.client, status=Appointment.STATUS_COMPLETED
            ).count()

            data = {
                "id": appointment.id,
                "client_name": f"{appointment.client.first_name} {appointment.client.last_name}",
                "first_name": appointment.client.first_name,
                "last_name": appointment.client.last_name,
                "client_phone": appointment.client.phone or "не указан",
                "client_email": appointment.client.email or "не указан",
                "service_name": appointment.service.title,
                "master_name": appointment.master.name,
                "datetime": appointment.datetime_start.strftime("%d.%m.%Y %H:%M"),
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
            log.info(f"Seeded appointment cache for ID={appointment_id}")
            return True

        except Exception as e:
            log.error(f"Failed to seed appointment cache for ID={appointment_id}: {e}")
            return False

    @classmethod
    def seed_contact_request(cls, request_id: int, extra_data: dict[str, Any] | None = None) -> bool:
        """
        Fetches contact request data and saves a JSON snapshot to Redis.
        """
        from features.main.models.contact_request import ContactRequest

        try:
            request = ContactRequest.objects.select_related("client").get(id=request_id)

            data = {
                "request_id": request.id,
                "first_name": request.client.first_name,
                "last_name": request.client.last_name,
                "contact_value": request.client.phone or request.client.email or "не указан",
                "contact_type": "phone" if request.client.phone else "email",
                "topic": request.get_topic_display(),
                "message": request.message,
                "created_at": request.created_at.strftime("%d.%m.%Y %H:%M"),
            }

            if extra_data:
                data.update(extra_data)

            # Note: The Bot currently expects ContactNotificationPayload to have {request_id, text}
            data["text"] = data.get("message", "")

            key = f"{cls.CONTACT_CACHE_PREFIX}{request_id}"
            cls.get_redis_client().set(key, json.dumps(data, ensure_ascii=False), ex=cls.TTL)
            log.info(f"Seeded contact cache for ID={request_id}")
            return True

        except Exception as e:
            log.error(f"Failed to seed contact cache for ID={request_id}: {e}")
            return False
