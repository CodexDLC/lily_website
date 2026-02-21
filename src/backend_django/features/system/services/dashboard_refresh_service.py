from asgiref.sync import sync_to_async
from features.main.models.contact_request import ContactRequest
from loguru import logger as log

from ..redis_managers.admin_dashboard_manager import AdminDashboardManager


class DashboardRefreshService:
    """
    Service for refreshing admin dashboard data in Redis.
    """

    @classmethod
    def _aggregate_data_sync(cls):
        """
        Synchronous part of aggregation to safely use Django ORM.
        """
        # 1. Summary Stats
        summary_categories = []

        # Contact Request Topics
        topic_map = {
            ContactRequest.TOPIC_GENERAL: "Общие вопросы",
            ContactRequest.TOPIC_BOOKING: "Вопросы по бронированию",
            ContactRequest.TOPIC_JOB: "Работа / Карьера",
            ContactRequest.TOPIC_OTHER: "Прочее",
        }

        for topic_id, topic_name in topic_map.items():
            summary_categories.append(
                {
                    "category_id": topic_id,
                    "category_name": topic_name,
                    "total_count": ContactRequest.objects.filter(topic=topic_id).count(),
                    "unread_count": ContactRequest.objects.filter(topic=topic_id, is_processed=False).count(),
                }
            )

        # 2. Details (Latest 500 records)
        details_data = []

        # Latest Contact Requests
        requests = ContactRequest.objects.select_related("client").order_by("-created_at")[:500]
        for req in requests:
            details_data.append(
                {
                    "id": req.id,
                    "topic": req.topic,
                    "first_name": req.client.first_name,
                    "phone": req.client.phone,
                    "message_preview": req.message[:50] + ("..." if len(req.message) > 50 else ""),
                    "message": req.message,
                    "is_processed": req.is_processed,
                    "created_at": req.created_at.isoformat(),
                }
            )

        return {"categories": summary_categories}, details_data

    @classmethod
    async def refresh_contacts(cls):
        """
        Refreshes 'contacts' feature data: summary and latest details.
        """
        try:
            summary_data, details_data = await sync_to_async(cls._aggregate_data_sync)()

            # 3. Save to Redis
            AdminDashboardManager.save_summary("contacts", summary_data)
            AdminDashboardManager.save_details("contacts", details_data)
            log.info(
                f"DashboardRefreshService | Refreshed 'contacts' (stats={len(summary_data['categories'])}, details={len(details_data)})"
            )
        except Exception as e:
            log.error(f"DashboardRefreshService | Error refreshing contacts: {e}")
            raise

    @classmethod
    async def refresh_all(cls):
        """
        Refreshes all dashboard features.
        """
        await cls.refresh_contacts()
        # Add more features here as needed
