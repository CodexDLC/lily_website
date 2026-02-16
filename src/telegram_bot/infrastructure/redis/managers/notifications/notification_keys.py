class NotificationKeys:
    """
    Ключи для Redis, используемые в фиче уведомлений.
    """

    @staticmethod
    def get_appointment_cache_key(appointment_id: int | str) -> str:
        """
        Ключ для временного хранения данных заявки (JSON).
        Пример: notifications:cache:123
        """
        return f"notifications:cache:{appointment_id}"
