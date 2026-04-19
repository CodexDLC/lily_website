import json
from typing import Any

from django_redis import get_redis_connection
from loguru import logger as log


class AdminDashboardManager:
    """
    Manager for saving dashboard snapshots (summary/details) to Redis.
    Matches the keys expected by the Telegram Bot's AdminCacheManager.
    """

    SUMMARY_PREFIX = "admin:summary:"
    DETAILS_PREFIX = "admin:details:"

    TTL = 3600  # 1 hour

    @staticmethod
    def get_redis_client():
        return get_redis_connection("default")

    @classmethod
    def save_summary(cls, feature_key: str, data: dict[str, Any]) -> bool:
        """
        Saves summary statistics for a feature.
        """
        key = f"{cls.SUMMARY_PREFIX}{feature_key}"
        try:
            cls.get_redis_client().set(key, json.dumps(data, ensure_ascii=False), ex=cls.TTL)
            log.debug(f"AdminDashboardManager | Saved summary for {feature_key}")
            return True
        except Exception as e:
            log.error(f"AdminDashboardManager | Error saving summary for {feature_key}: {e}")
            return False

    @classmethod
    def save_details(cls, feature_key: str, data: list[dict[str, Any]]) -> bool:
        """
        Saves detailed JSON dump for a feature.
        """
        key = f"{cls.DETAILS_PREFIX}{feature_key}"
        try:
            cls.get_redis_client().set(key, json.dumps(data, ensure_ascii=False), ex=cls.TTL)
            log.debug(f"AdminDashboardManager | Saved details for {feature_key}")
            return True
        except Exception as e:
            log.error(f"AdminDashboardManager | Error saving details for {feature_key}: {e}")
            return False

    @classmethod
    def clear_cache(cls, feature_key: str) -> bool:
        """
        Deletes summary and details keys for a feature.
        """
        summary_key = f"{cls.SUMMARY_PREFIX}{feature_key}"
        details_key = f"{cls.DETAILS_PREFIX}{feature_key}"
        try:
            cls.get_redis_client().delete(summary_key, details_key)
            log.info(f"AdminDashboardManager | Cache cleared for feature='{feature_key}'")
            return True
        except Exception as e:
            log.error(f"AdminDashboardManager | Error clearing cache for {feature_key}: {e}")
            return False
