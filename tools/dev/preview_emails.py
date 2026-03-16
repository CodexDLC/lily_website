#!/usr/bin/env python
import argparse
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Try to import Markup from markupsafe (Jinja2 3.1+) or jinja2 (older versions)
try:
    from markupsafe import Markup
except ImportError:
    try:
        from jinja2 import Markup  # type: ignore[attr-defined, no-redef]
    except ImportError:

        def Markup(s: str) -> str:  # type: ignore[no-redef] # noqa: N802
            return s

# ═══════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_TEMPLATES_DIR = BASE_DIR / "src" / "workers" / "templates"

SMTP_HOST = "localhost"
SMTP_PORT = 1025
SENDER = "noreply@lily-salon.de"
RECEIVER = "dev@lily-salon.de"

# ═══════════════════════════════════════════
# Mock Data Generator
# ═══════════════════════════════════════════


def get_context_for_template(template_path: str) -> dict[str, Any]:
    """Returns specific mock data based on template type."""

    # Base common data
    base = {
        "site_url": "https://lily-salon.de",
        "logo_url": "https://pinlite.dev/media/storage/a3/65/a365b5fedad7fb5779bc5fcf63f00ebc19ed90808c4010a0fbec7207773ca95e.png",
        "greeting": "Guten Tag Anna,",
        "name": "Anna",
        "signature": "Herzliche Grüße,\nIhr LILY Salon Team",
    }

    # Specifics
    data: dict[str, Any] = {}
    if "booking" in template_path:
        data = {
            "service_name": "Maniküre Komplett",
            "date": "25.10.2023",
            "time": "14:30",
            "salon_address": "Berliner Str. 42, 10117 Berlin",
            "action_token": "uuid-for-testing",
            "link_reschedule": "https://lily-salon.de/booking/reschedule/test-token",
            "link_booking": "https://lily-salon.de/booking",
            "intro_text": "Wir freuen uns auf Ihren Besuch morgen!",
            "email_body": "Schade, dass Sie Ihren Termin heute nicht wahrnehmen konnten. Wir hoffen, es ist alles in Ordnung.",
            "cancellation_reason": "Terminkonflikt",
            "items": [
                {"name": "Maniküre", "price": "45.00 €", "time": "14:30", "master_name": "Elena"},
                {"name": "Pediküre", "price": "35.00 €", "time": "15:30", "master_name": "Elena"},
            ],
            "total_price": "80.00 €",
        }
    elif "marketing" in template_path:
        data = {
            "body_text": "Es ist schon 3 Wochen her seit Ihrem letzten Besuch. Gönnen Sie sich wieder einmal eine Auszeit!",
        }
    elif "contacts" in template_path:
        data = {
            "reply_text": "Vielen Dank für Ihre Nachricht. Wir haben Ihr Anliegen успешно bearbeitet и freuen uns auf Ihre Bestätigung.",
            "history_text": "Frage: Haben Sie morgen noch einen Termin frei?\nAntwort: Ja, um 14:00 Uhr.",
            "request_id": "REQ-777",
            "body_text": "Vielen Dank für Ihre Anfrage über unser Kontaktformular. Wir haben Ihre Nachricht erhalten и werden uns so schnell wie möglich mit Ihnen in Verbindung setzen.",
        }

    # Combine
    ctx = {**base, **data}
    return {**ctx, "data": ctx}


# ═══════════════════════════════════════════
# Logic
# ═══════════════════════════════════════════


def nl2br_filter(value: str) -> Any:
    if not value:
        return ""
    result = re.sub(r"\r\n|\r|\n", "<br>", value)
    return Markup(result)


def find_templates(templates_dir: Path) -> list[str]:
    found = []
    for path in templates_dir.rglob("*.html"):
        if path.name.startswith("_") or path.name.startswith("base"):
            continue
        rel_path = path.relative_to(templates_dir)
        found.append(str(rel_path).replace("\\", "/"))
    return sorted(found)


def send_email(server: smtplib.SMTP, template_path: str, env: Environment) -> None:
    try:
        template = env.get_template(template_path)
        context = get_context_for_template(template_path)
        html_content = template.render(context)

        msg = MIMEMultipart()
        msg["From"] = SENDER
        msg["To"] = RECEIVER
        msg["Subject"] = f"🧪 Preview: {template_path}"
        msg.attach(MIMEText(html_content, "html"))

        server.sendmail(SENDER, RECEIVER, msg.as_string())
        print(f"✅ Sent: {template_path}")
    except Exception as e:
        print(f"❌ Error {template_path}: {e}")


def interactive_mode(templates_dir: Path) -> None:
    if not templates_dir.exists():
        print(f"❌ Error: Templates directory not found at {templates_dir}")
        return

    env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=select_autoescape(["html", "xml"]))
    env.filters["nl2br"] = nl2br_filter

    templates = find_templates(templates_dir)
    while True:
        print("\n--- Email Preview Tool ---")
        print("0. Send ALL templates")
        for i, t in enumerate(templates, 1):
            print(f"{i}. {t}")
        print("q. Quit")

        choice = input("\nSelect an option: ").strip().lower()
        if choice == "q":
            break

        to_send = (
            templates
            if choice == "0"
            else ([templates[int(choice) - 1]] if choice.isdigit() and 1 <= int(choice) <= len(templates) else [])
        )
        if not to_send:
            continue

        print(f"\n🚀 Connecting to Mailpit at {SMTP_HOST}:{SMTP_PORT}...")
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=5) as server:
                for t_path in to_send:
                    send_email(server, t_path, env)
            print("\nDone. Check Mailpit Web UI (http://localhost:8025)")
        except Exception as e:
            print(f"🚫 Error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=str(DEFAULT_TEMPLATES_DIR))
    args = parser.parse_args()
    interactive_mode(Path(args.path))
