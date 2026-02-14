from src.workers.core.email_client import AsyncEmailClient
from src.workers.core.template_renderer import TemplateRenderer


class NotificationService:
    def __init__(
        self,
        templates_dir: str,
        site_url: str,
        logo_url: str | None = None,
        smtp_host: str | None = None,
        smtp_port: int | None = None,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
        smtp_from_email: str | None = None,
        smtp_use_tls: bool = True,  # smtp_use_ssl удален
        url_path_confirm: str | None = None,
        url_path_cancel: str | None = None,
        url_path_reschedule: str | None = None,
        url_path_contact_form: str | None = None,
    ):
        # Проверяем наличие обязательных настроек SMTP для клиента
        if not all([smtp_host, smtp_port, smtp_user, smtp_password, smtp_from_email]):
            raise ValueError("SMTP settings are incomplete. Check your environment variables.")

        self.email_client = AsyncEmailClient(
            smtp_host=smtp_host,  # type: ignore[arg-type]
            smtp_port=smtp_port,  # type: ignore[arg-type]
            smtp_user=smtp_user,  # type: ignore[arg-type]
            smtp_password=smtp_password,  # type: ignore[arg-type]
            smtp_from_email=smtp_from_email,  # type: ignore[arg-type]
            smtp_use_tls=smtp_use_tls,
        )
        self.renderer = TemplateRenderer(templates_dir)
        self.site_url = site_url
        self.logo_url = logo_url

        # Сохраняем URL-пути
        self.url_path_confirm = url_path_confirm
        self.url_path_cancel = url_path_cancel
        self.url_path_reschedule = url_path_reschedule
        self.url_path_contact_form = url_path_contact_form

    def _enrich_context(self, data: dict) -> dict:
        """
        Обогащает пришедшие данные глобальными настройками и вычисляет приветствие.
        Также формирует полные динамические URL, используя токены.
        """
        context = data.copy()

        context["site_url"] = self.site_url
        context["logo_url"] = self.logo_url

        # Формируем contact_form_url динамически
        if self.site_url and self.url_path_contact_form:
            context["contact_form_url"] = f"{self.site_url}{self.url_path_contact_form}"
        else:
            context["contact_form_url"] = "#"  # Заглушка

        # Логика приветствия
        if "name" in context and "greeting" not in context:
            is_new = context.get("is_new_client", False)
            name = context["name"]
            if is_new:
                context["greeting"] = f"Sehr geehrte(r) {name},"
            else:
                context["greeting"] = f"Guten Tag {name},"

        # --- Формирование динамических URL для действий с токенами ---
        action_token = data.get("action_token")  # Ожидаем общий токен для действия (отмена/перенос)

        # Ссылка на подтверждение (если есть)
        if self.url_path_confirm and action_token:
            context["link_confirm"] = f"{self.site_url}{self.url_path_confirm.format(token=action_token)}"
        else:
            context["link_confirm"] = "#"

        # Ссылка на отмену
        if self.url_path_cancel and action_token:
            context["link_cancel"] = f"{self.site_url}{self.url_path_cancel.format(token=action_token)}"
        else:
            context["link_cancel"] = "#"

        # Ссылка на перенос/новую запись (всегда ведет на общую форму бронирования)
        if self.url_path_reschedule:
            context["link_reschedule"] = f"{self.site_url}{self.url_path_reschedule}"
            context["link_calendar"] = f"{self.site_url}{self.url_path_reschedule}"  # Для reengagement
        else:
            context["link_reschedule"] = "#"
            context["link_calendar"] = "#"

        # Удаляем логику для конкретных слотов, так как теперь всегда ведем на общую форму
        # Эти переменные больше не будут формироваться, но оставим их в шаблонах для совместимости
        context["next_week_link"] = context["link_reschedule"]  # Ведет на общую форму
        context["slot_1_link"] = context["link_reschedule"]
        context["slot_2_link"] = context["link_reschedule"]
        context["slot_3_link"] = context["link_reschedule"]
        context["slot_4_link"] = context["link_reschedule"]

        # Очищаем данные слотов, если они были переданы, чтобы не сбивать с толку
        context.pop("alternative_slots", None)
        context.pop("next_week_data", None)
        context.pop("slots", None)

        return context

    async def send_notification(self, email: str, subject: str, template_name: str, data: dict):
        """
        Универсальный метод отправки уведомления.
        """
        full_context = self._enrich_context(data)
        html_content = self.renderer.render(template_name, full_context)
        await self.email_client.send_email(email, subject, html_content)
