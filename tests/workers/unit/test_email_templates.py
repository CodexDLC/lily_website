from pathlib import Path

from workers.core.base_module.template_renderer import TemplateRenderer


def test_group_booking_email_is_pending_receipt_not_confirmation():
    templates_dir = Path(__file__).resolve().parents[3] / "src" / "workers" / "templates"
    renderer = TemplateRenderer(str(templates_dir))

    html = renderer.render(
        "booking/bk_group_booking.html",
        {
            "site_url": "https://lily.example",
            "logo_url": "https://lily.example/logo.png",
            "greeting": "Hallo Anna,",
            "date": "24.04.2026",
            "items": [
                {
                    "time": "09:30",
                    "service_name": "Nagelverlängerungen",
                    "master_name": "Lilya",
                    "price": "0.00",
                },
                {
                    "time": "11:15",
                    "service_name": "Smart-Pediküre Komplett",
                    "master_name": "Lilya",
                    "price": "0.00",
                },
            ],
            "total_price": "0.00",
        },
    )

    assert "STATUS: IN PRÜFUNG" in html
    assert "Ihre Anfrage (unverbindlich)" in html
    assert "Diese E-Mail dient nur zur Information über den Eingang Ihrer Anfrage" in html
    assert "stellt noch keine feste Buchung dar" in html
    assert "Angefragte Termine" in html
    assert "TERMINBESTÄTIGUNG" not in html
    assert "Vielen Dank für Ihre Buchung" not in html
    assert "Wir freuen uns auf Ihren Besuch" not in html
