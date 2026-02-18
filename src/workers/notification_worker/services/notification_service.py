from datetime import datetime, timedelta
from urllib.parse import quote

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
        )
        self.renderer = TemplateRenderer(templates_dir)
        self.site_url = site_url
        self.logo_url = logo_url

        self.url_path_confirm = url_path_confirm
        self.url_path_cancel = url_path_cancel
        self.url_path_reschedule = url_path_reschedule
        self.url_path_contact_form = url_path_contact_form

    def _translit(self, text: str) -> str:
        """Транслитерация для имен."""
        translit_map = str.maketrans(
            {
                "а": "a",
                "б": "b",
                "в": "v",
                "г": "g",
                "д": "d",
                "е": "e",
                "ё": "yo",
                "ж": "zh",
                "з": "z",
                "и": "i",
                "й": "y",
                "к": "k",
                "л": "l",
                "м": "m",
                "н": "n",
                "о": "o",
                "п": "p",
                "р": "r",
                "с": "s",
                "т": "t",
                "у": "u",
                "ф": "f",
                "х": "kh",
                "ц": "ts",
                "ч": "ch",
                "ш": "sh",
                "щ": "shch",
                "ъ": "",
                "ы": "y",
                "ь": "",
                "э": "e",
                "ю": "yu",
                "я": "ya",
                "А": "A",
                "Б": "B",
                "В": "V",
                "Г": "G",
                "Д": "D",
                "Е": "E",
                "Ё": "Yo",
                "Ж": "Zh",
                "З": "Z",
                "И": "I",
                "Й": "Y",
                "К": "K",
                "Л": "L",
                "М": "M",
                "Н": "N",
                "О": "O",
                "П": "P",
                "Р": "R",
                "С": "S",
                "Т": "T",
                "У": "U",
                "Ф": "F",
                "Х": "Kh",
                "Ц": "Ts",
                "Ч": "Ch",
                "Ш": "Sh",
                "Щ": "Shch",
                "Ъ": "",
                "Ы": "Y",
                "Ь": "",
                "Э": "E",
                "Ю": "Yu",
                "Я": "Ya",
            }
        )
        return text.translate(translit_map)

    def get_sms_text(self, data: dict) -> str:
        """Генерирует текст SMS."""
        first_name = data.get("first_name", "Guest")
        dt_str = str(data.get("datetime", ""))
        parts = dt_str.split(" ")
        date = parts[0] if len(parts) > 0 else dt_str
        time = parts[1] if len(parts) > 1 else ""

        clean_name = self._translit(first_name)
        return f"Hallo {clean_name}, Ihr Termin am {date} um {time} im Lily Beauty Salon ist bestätigt. Wir freuen uns на Sie!"

    def _generate_google_calendar_url(self, data: dict) -> str:
        """Генерирует ссылку для Google Calendar."""
        try:
            service_name = data.get("service_name", "Beauty Termin")
            dt_str = data.get("datetime")  # Используем исходную строку datetime
            duration = int(data.get("duration_minutes", 30))

            if not dt_str:
                return ""

            # Парсим из формата "DD.MM.YYYY HH:MM"
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

        # Разделяем дату и время для отображения в таблице письма
        dt_str = str(context.get("datetime", ""))
        if " " in dt_str:
            parts = dt_str.split(" ")
            context["date"] = parts[0]
            context["time"] = parts[1]
        else:
            context["date"] = context.get("date", dt_str)
            context["time"] = context.get("time", "")

        clean_site_url = self.site_url.rstrip("/")
        context["site_url"] = clean_site_url

        if self.logo_url:
            if self.logo_url.startswith("http"):
                context["logo_url"] = self.logo_url
            else:
                path = self.logo_url if self.logo_url.startswith("/") else f"/{self.logo_url}"
                context["logo_url"] = f"{clean_site_url}{path}"
        else:
            context["logo_url"] = f"{clean_site_url}/static/img/_source/logo_lily.png"

        if self.url_path_contact_form:
            path = (
                self.url_path_contact_form
                if self.url_path_contact_form.startswith("/")
                else f"/{self.url_path_contact_form}"
            )
            context["contact_form_url"] = f"{clean_site_url}{path}"
        else:
            context["contact_form_url"] = "#"

        # Генерируем ссылку на календарь (теперь она использует исходный datetime)
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
        full_context = self.enrich_email_context(data)
        html_content = self.renderer.render(template_name, full_context)
        await self.email_client.send_email(email, subject, html_content)
