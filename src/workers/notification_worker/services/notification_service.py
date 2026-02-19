from datetime import datetime, timedelta
from urllib.parse import quote

from src.shared.utils.text import transliterate
from src.workers.core.base_module.email_client import AsyncEmailClient
from src.workers.core.base_module.template_renderer import TemplateRenderer


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
        sendgrid_api_key: str | None = None,
        url_path_confirm: str | None = None,
        url_path_cancel: str | None = None,
        url_path_reschedule: str | None = None,
        url_path_contact_form: str | None = None,
    ):
        if not all([smtp_host, smtp_port, smtp_from_email]):
            raise ValueError("Core SMTP settings are missing.")

        assert smtp_host is not None
        assert smtp_port is not None
        assert smtp_from_email is not None

        self.email_client = AsyncEmailClient(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            smtp_from_email=smtp_from_email,
            smtp_use_tls=smtp_use_tls,
            sendgrid_api_key=sendgrid_api_key,
        )
        self.renderer = TemplateRenderer(templates_dir)
        self.site_url = site_url.rstrip("/")
        self.logo_url = logo_url

        self.url_path_confirm = url_path_confirm
        self.url_path_cancel = url_path_cancel
        self.url_path_reschedule = url_path_reschedule
        self.url_path_contact_form = url_path_contact_form

    def get_absolute_logo_url(self) -> str | None:
        if not self.logo_url:
            return f"{self.site_url}/static/img/_source/logo_lily.png"
        if self.logo_url.startswith("http"):
            return self.logo_url
        path = self.logo_url if self.logo_url.startswith("/") else f"/{self.logo_url}"
        return f"{self.site_url}{path}"

    def get_sms_text(self, data: dict) -> str:
        """Генерирует текст SMS."""
        first_name = data.get("first_name", "Guest")
        dt_str = data.get("datetime", "")
        try:
            dt_obj = datetime.strptime(dt_str, "%d.%m.%Y %H:%M")
            date = dt_obj.strftime("%d.%m.%Y")
            time = dt_obj.strftime("%H:%M")
        except (ValueError, TypeError):  # Исправлено: специфичные исключения
            date = dt_str
            time = ""

        clean_name = transliterate(first_name)
        return f"Hallo {clean_name}, Ihr Termin am {date} um {time} im Lily Beauty Salon ist bestätigt. Wir freuen uns на Sie!"

    def _generate_google_calendar_url(self, data: dict) -> str:
        """Генерирует ссылку для Google Calendar."""
        try:
            service_name = data.get("service_name", "Beauty Termin")
            dt_str = data.get("datetime")
            duration = int(data.get("duration_minutes", 30))
            if not dt_str:
                return ""
            start_dt = datetime.strptime(dt_str, "%d.%m.%Y %H:%M")
            end_dt = start_dt + timedelta(minutes=duration)
            fmt = "%Y%m%dT%H%M%S"
            dates = f"{start_dt.strftime(fmt)}/{end_dt.strftime(fmt)}"
            base_url = "https://www.google.com/calendar/render?action=TEMPLATE"
            params = {
                "text": f"LILY Salon: {service_name}",
                "dates": dates,
                "details": f"Ihr Termin im LILY Beauty Salon. Web: {self.site_url}",
                "location": "Lohmannstraße 111, 06366 Köthen (Anhalt)",
                "sf": "true",
                "output": "xml",
            }
            query_str = "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
            return f"{base_url}&{query_str}"
        except Exception:
            return ""

    def enrich_email_context(self, data: dict) -> dict:
        """Подготавливает полный контекст для Email шаблона."""
        context = data.copy()
        dt_str = str(context.get("datetime", ""))
        try:
            dt_obj = datetime.strptime(dt_str, "%d.%m.%Y %H:%M")
            context["date"] = dt_obj.strftime("%d.%m.%Y")
            context["time"] = dt_obj.strftime("%H:%M")
        except (ValueError, TypeError):  # Исправлено: специфичные исключения
            context["date"] = dt_str
            context["time"] = ""
        context["site_url"] = self.site_url
        context["logo_url"] = self.get_absolute_logo_url()
        if self.url_path_contact_form:
            path = (
                self.url_path_contact_form
                if self.url_path_contact_form.startswith("/")
                else f"/{self.url_path_contact_form}"
            )
            context["contact_form_url"] = f"{self.site_url}{path}"
        else:
            context["contact_form_url"] = "#"
        context["calendar_url"] = self._generate_google_calendar_url(data)
        if "name" in context and "greeting" not in context:
            visits = int(context.get("visits_count", 0))
            name = context["name"]
            if visits == 0:
                context["greeting"] = f"Sehr geehrte/r {name},"
            elif 1 <= visits <= 4:
                context["greeting"] = f"Liebe/r {name},"
            else:
                context["greeting"] = f"Hallo {name},"
        action_token = data.get("action_token")
        if self.url_path_confirm and action_token:
            context["link_confirm"] = f"{self.site_url}{self.url_path_confirm.format(token=action_token)}"
        else:
            context["link_confirm"] = "#"
        if self.url_path_cancel and action_token:
            context["link_cancel"] = f"{self.site_url}{self.url_path_cancel.format(token=action_token)}"
        else:
            context["link_cancel"] = "#"
        if self.url_path_reschedule:
            path = (
                self.url_path_reschedule if self.url_path_reschedule.startswith("/") else f"/{self.url_path_reschedule}"
            )
            context["link_reschedule"] = f"{self.site_url}{path}"
            context["link_calendar"] = f"{self.site_url}{path}"
        else:
            context["link_reschedule"] = "#"
            context["link_calendar"] = "#"
        return context

    async def send_notification(self, email: str, subject: str, template_name: str, data: dict):
        full_context = self.enrich_email_context(data)
        html_content = self.renderer.render(template_name, full_context)
        await self.email_client.send_email(email, subject, html_content)
