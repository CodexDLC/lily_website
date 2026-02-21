class AdminKeys:
    """
    Ключи для Redis, используемые в модуле администратора (Dashboard).
    """

    @staticmethod
    def get_summary_key(domain: str) -> str:
        """
        Ключ для хранения агрегированных сводных данных.
        domain: 'contacts' или 'appointments'
        Пример: admin:summary:contacts
        """
        return f"admin:summary:{domain}"

    @staticmethod
    def get_details_key(domain: str) -> str:
        """
        Ключ для хранения JSON-дампа последних объектов.
        domain: 'contacts' или 'appointments'
        Пример: admin:details:contacts
        """
        return f"admin:details:{domain}"
