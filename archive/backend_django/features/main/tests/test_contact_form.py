"""Unit tests for ContactForm validation."""

import pytest
from features.main.forms import ContactForm


def _valid_data():
    return {
        "first_name": "Anna",
        "last_name": "Test",
        "contact_type": "email",
        "contact_value": "anna@test.de",
        "topic": "general",
        "message": "Hello",
        "dsgvo_consent": True,
        "consent_marketing": False,
    }


@pytest.mark.unit
class TestContactForm:
    def test_valid_form_is_valid(self):
        form = ContactForm(data=_valid_data())
        assert form.is_valid(), form.errors

    def test_missing_first_name_invalid(self):
        data = _valid_data()
        del data["first_name"]
        assert not ContactForm(data=data).is_valid()

    def test_missing_last_name_invalid(self):
        data = _valid_data()
        del data["last_name"]
        assert not ContactForm(data=data).is_valid()

    def test_invalid_email_format_adds_error_to_contact_value(self):
        data = _valid_data()
        data["contact_value"] = "not-an-email"
        form = ContactForm(data=data)
        assert not form.is_valid()
        assert "contact_value" in form.errors

    def test_valid_email_passes_validation(self):
        data = _valid_data()
        data["contact_value"] = "valid@email.de"
        form = ContactForm(data=data)
        assert form.is_valid(), form.errors

    def test_dsgvo_consent_required(self):
        data = _valid_data()
        data["dsgvo_consent"] = False
        form = ContactForm(data=data)
        assert not form.is_valid()
        assert "dsgvo_consent" in form.errors

    def test_message_not_required(self):
        data = _valid_data()
        data["message"] = ""
        form = ContactForm(data=data)
        assert form.is_valid(), form.errors

    def test_consent_marketing_not_required(self):
        data = _valid_data()
        del data["consent_marketing"]
        form = ContactForm(data=data)
        assert form.is_valid(), form.errors

    def test_missing_contact_value_invalid(self):
        data = _valid_data()
        del data["contact_value"]
        form = ContactForm(data=data)
        assert not form.is_valid()
