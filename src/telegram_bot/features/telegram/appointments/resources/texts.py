# Текстовые ресурсы для фичи Appointments.
# Простые строки без i18n — фича внутренняя (только admin).


class AppointmentsTexts:
    @staticmethod
    def btn_back() -> str:
        return "🔙 Назад"

    @staticmethod
    def btn_dashboard() -> str:
        return "📅 Записи"

    @staticmethod
    def btn_soon() -> str:
        return "🔔 Скоро"

    @staticmethod
    def btn_open_tma() -> str:
        return "📂 Открыть (TMA)"

    @staticmethod
    def btn_create_tma() -> str:
        return "➕ Создать (TMA)"
