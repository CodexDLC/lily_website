from datetime import datetime, timedelta
from urllib.parse import quote

from loguru import logger as log

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
        if not smtp_host or not smtp_port or not smtp_from_email:
            raise ValueError("Core SMTP settings are missing.")

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

    # --- Core Sending Methods ---

    async def send_notification(self, email: str, subject: str, template_name: str, data: dict):
        """Base method for sending any email notification."""
        full_context = self.enrich_email_context(data)
        full_template_path = self.resolve_template_path(template_name)

        log.debug(f"NotificationService: Rendering {full_template_path} for {email}")
        html_content = self.renderer.render(full_template_path, full_context)
        await self.email_client.send_email(email, subject, html_content)

    # --- Specific Helpers (Legacy/Convenience) ---

    async def send_booking_confirmation(self, recipient_email: str, client_name: str, context: dict):
        """Sends a standard booking confirmation."""
        data = context.copy()
        data["first_name"] = client_name
        await self.send_notification(recipient_email, "Terminbestätigung - LILY Beauty Salon", "bk_confirmation", data)

    async def send_booking_cancellation(self, recipient_email: str, client_name: str, context: dict):
        """Sends a booking cancellation notice."""
        data = context.copy()
        data["first_name"] = client_name
        await self.send_notification(recipient_email, "Terminstornierung - LILY Beauty Salon", "bk_cancellation", data)

    async def send_booking_no_show(self, recipient_email: str, client_name: str, context: dict):
        """Sends a no-show notification."""
        data = context.copy()
        data["first_name"] = client_name
        await self.send_notification(recipient_email, "Vermisster Termin - LILY Beauty Salon", "bk_no_show", data)

    async def send_universal(
        self, recipient_email: str, first_name: str, template_name: str, subject: str, context_data: dict, **kwargs
    ):
        """Universal gateway for any template."""
        data = context_data.copy()
        data["first_name"] = first_name
        await self.send_notification(recipient_email, subject, template_name, data)

    # --- Internal Logic ---

    def resolve_template_path(self, template_name: str) -> str:
        if template_name.startswith("bk_"):
            return f"booking/{template_name}.html"
        if template_name.startswith("ct_"):
            return f"contacts/{template_name}.html"
        if template_name.startswith("mk_"):
            return f"marketing/{template_name}.html"
        return f"{template_name}.html" if not template_name.endswith(".html") else template_name

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
            date_val = dt_obj.strftime("%d.%m.%Y")
            time_val = dt_obj.strftime("%H:%M")
        except (ValueError, TypeError):
            date_val = dt_str
            time_val = ""

        clean_name = transliterate(first_name)
        return f"Hallo {clean_name}, Ihr Termin am {date_val} um {time_val} im Lily Beauty Salon ist bestätigt. Wir freuen uns на Sie!"

    def enrich_email_context(self, data: dict) -> dict:
        context = data.copy()
        context["data"] = data

        dt_str = str(context.get("datetime", ""))
        try:
            dt_obj = datetime.strptime(dt_str, "%d.%m.%Y %H:%M")
            context["date"] = dt_obj.strftime("%d.%m.%Y")
            context["time"] = dt_obj.strftime("%H:%M")
        except (ValueError, TypeError):
            context["date"] = context.get("booking_date", dt_str)
            context["time"] = ""

        context["site_url"] = self.site_url
        context["logo_url"] = self.get_absolute_logo_url()
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

        return context

    def _generate_google_calendar_url(self, data: dict) -> str:
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
