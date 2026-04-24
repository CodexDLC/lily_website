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

    @staticmethod
    def get_contact_cache_key(request_id: int | str) -> str:
        """
        Ключ для временного хранения данных контактной заявки.
        Пример: notifications:contact_cache:1
        """
        return f"notifications:contact_cache:{request_id}"
