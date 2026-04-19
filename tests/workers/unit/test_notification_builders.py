from urllib.parse import parse_qs, urlparse

from workers.notification_worker.services.notification_service import CalendarUrlBuilder, MessageBuilder


class TestMessageBuilder:
    def test_get_sms_text_standard(self):
        data = {"first_name": "Anna", "datetime": "20.04.2026 10:00"}
        text = MessageBuilder.get_sms_text(data, site_name="LILY")
        assert "Hallo Anna" in text
        assert "20.04.2026" in text
        assert "10:00" in text
        assert "LILY" in text

    def test_get_sms_text_transliteration(self):
        # Assuming transliterate converts non-ascii or just works
        data = {
            "first_name": "Юлия",  # Russian, should be transliterated
            "datetime": "20.04.2026 10:00",
        }
        text = MessageBuilder.get_sms_text(data)
        assert "Hallo Yuliya" in text or "Hallo Iuliia" in text  # depends on library

    def test_get_sms_text_invalid_date(self):
        data = {"first_name": "Anna", "datetime": "invalid-date"}
        text = MessageBuilder.get_sms_text(data)
        assert "Hallo Anna" in text
        assert "invalid-date" in text  # fallback behavior

    def test_get_sms_text_missing_name(self):
        data = {"datetime": "20.04.2026 10:00"}
        text = MessageBuilder.get_sms_text(data)
        assert "Hallo Guest" in text


class TestCalendarUrlBuilder:
    def test_build_url_standard(self):
        data = {
            "service_name": "Manicure",
            "duration_minutes": 60,
            "datetime": "20.04.2026 10:00",
            "salon_address": "Test Str. 1",
        }
        url = CalendarUrlBuilder.build_url(data, site_url="https://lily.de")

        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        assert params["text"][0] == "LILY Salon: Manicure"
        assert params["location"][0] == "Test Str. 1"
        assert "20260420T100000" in params["dates"][0]
        assert "20260420T110000" in params["dates"][0]  # +60 min

    def test_build_url_no_address(self):
        data = {"datetime": "20.04.2026 10:00"}
        url = CalendarUrlBuilder.build_url(data, site_url="https://lily.de")
        assert "location" not in url

    def test_build_url_missing_date(self):
        data = {}
        url = CalendarUrlBuilder.build_url(data, site_url="https://lily.de")
        assert url == ""

    def test_build_url_invalid_date(self):
        data = {"datetime": "wrong"}
        url = CalendarUrlBuilder.build_url(data, site_url="https://lily.de")
        assert url == ""
