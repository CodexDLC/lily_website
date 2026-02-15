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
        smtp_use_tls: bool = False,
        url_path_confirm: str | None = None,
        url_path_cancel: str | None = None,
        url_path_reschedule: str | None = None,
        url_path_contact_form: str | None = None,
    ):
        # Проверяем наличие минимально необходимых настроек SMTP
        if not all([smtp_host, smtp_port, smtp_from_email]):
            raise ValueError("Core SMTP settings (host, port, from_email) are missing.")

        self.email_client = AsyncEmailClient(
            smtp_host=smtp_host,  # type: ignore[arg-type]
            smtp_port=smtp_port,  # type: ignore[arg-type]
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            smtp_from_email=smtp_from_email,
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
        """
        context = data.copy()

        # Очищаем базовый URL от слэша на конце
        clean_site_url = self.site_url.rstrip("/")
        context["site_url"] = clean_site_url

        # Логика формирования logo_url
        if self.logo_url:
            if self.logo_url.startswith("http"):
                context["logo_url"] = self.logo_url
            else:
                # Если путь относительный, приклеиваем к site_url
                path = self.logo_url if self.logo_url.startswith("/") else f"/{self.logo_url}"
                context["logo_url"] = f"{clean_site_url}{path}"
        else:
            # Фолбэк на PNG в статике
            context["logo_url"] = f"{clean_site_url}/static/img/_source/logo_lily.png"

        # Формируем contact_form_url динамически
        if self.url_path_contact_form:
            path = (
                self.url_path_contact_form
                if self.url_path_contact_form.startswith("/")
                else f"/{self.url_path_contact_form}"
            )
            context["contact_form_url"] = f"{clean_site_url}{path}"
        else:
            context["contact_form_url"] = "#"

        # Персонализированное приветствие
        if "name" in context and "greeting" not in context:
            visits = int(context.get("visits_count", 0))
            name = context["name"]

            if visits == 0:
                context["greeting"] = f"Sehr geehrte/r {name},"
            elif 1 <= visits <= 4:
                context["greeting"] = f"Liebe/r {name},"
            else:
                context["greeting"] = f"Hallo {name},"

        # --- Формирование динамических URL для действий ---
        action_token = data.get("action_token")

        if self.url_path_confirm and action_token:
            context["link_confirm"] = f"{clean_site_url}{self.url_path_confirm.format(token=action_token)}"
        else:
            context["link_confirm"] = "#"

        if self.url_path_cancel and action_token:
            context["link_cancel"] = f"{clean_site_url}{self.url_path_cancel.format(token=action_token)}"
        else:
            context["link_cancel"] = "#"

        if self.url_path_reschedule:
            path = (
                self.url_path_reschedule if self.url_path_reschedule.startswith("/") else f"/{self.url_path_reschedule}"
            )
            context["link_reschedule"] = f"{clean_site_url}{path}"
            context["link_calendar"] = f"{clean_site_url}{path}"
        else:
            context["link_reschedule"] = "#"
            context["link_calendar"] = "#"

        return context

    async def send_notification(self, email: str, subject: str, template_name: str, data: dict):
        """
        Универсальный метод отправки уведомления.
        """
        full_context = self._enrich_context(data)
        html_content = self.renderer.render(template_name, full_context)
        await self.email_client.send_email(email, subject, html_content)
