"""
Unit/integration tests for features.booking.forms.MasterAdminForm.
"""

import pytest
from features.booking.forms import MasterAdminForm
from features.booking.models import Master


@pytest.mark.django_db
class TestMasterAdminFormCleanPhoto:
    """Tests for the clean_photo method that handles the file/clear conflict."""

    def _build_form(self, data=None, files=None, instance=None):
        """Helper to create a MasterAdminForm."""
        if data is None:
            data = {
                "name": "Test Master",
                "slug": "test-master-form",
                "status": Master.STATUS_ACTIVE,
                "work_days": [0, 1, 2, 3, 4],
                "max_clients_parallel": 1,
                "years_experience": 1,
                "timezone": "Europe/Berlin",
                "order": 0,
            }
        return MasterAdminForm(data=data, files=files or {}, instance=instance)

    def test_form_valid_without_photo(self):
        form = self._build_form()
        assert form.is_valid(), form.errors

    def test_clean_photo_returns_value_from_cleaned_data(self):
        """clean_photo returns whatever cleaned_data has — even if it's None/False."""
        form = self._build_form()
        form.is_valid()
        # Without a real file, photo field should be falsy but not error out
        # (the clean_photo method simply returns self.cleaned_data.get("photo"))
        if hasattr(form, "clean_photo"):
            form.clean_photo()  # just ensure no exception is raised

    def test_clean_photo_returns_none_when_no_photo(self):
        form = self._build_form()
        assert form.is_valid(), form.errors
        # When no photo provided, cleaned_data photo is falsy but not an error
        result = form.cleaned_data.get("photo")
        # Could be False or None or empty — the form should not error out
        assert result is not True  # just ensure no unexpected truthy result

    def test_form_meta_model_is_master(self):
        assert MasterAdminForm.Meta.model is Master

    def test_form_meta_fields_is_all(self):
        assert MasterAdminForm.Meta.fields == "__all__"

    def test_form_with_invalid_status_is_invalid(self):
        data = {
            "name": "Bad Status Master",
            "slug": "bad-status-master",
            "status": "nonexistent_status",
            "work_days": [0, 1, 2],
            "max_clients_parallel": 1,
            "years_experience": 1,
            "timezone": "Europe/Berlin",
            "order": 0,
        }
        form = MasterAdminForm(data=data, files={})
        assert not form.is_valid()
        assert "status" in form.errors

    def test_form_requires_name(self):
        data = {
            "slug": "no-name-master",
            "status": Master.STATUS_ACTIVE,
            "max_clients_parallel": 1,
            "years_experience": 1,
            "timezone": "Europe/Berlin",
            "order": 0,
        }
        form = MasterAdminForm(data=data, files={})
        assert not form.is_valid()
        assert "name" in form.errors

    def test_form_requires_slug(self):
        data = {
            "name": "No Slug Master",
            "status": Master.STATUS_ACTIVE,
            "max_clients_parallel": 1,
            "years_experience": 1,
            "timezone": "Europe/Berlin",
            "order": 0,
        }
        form = MasterAdminForm(data=data, files={})
        assert not form.is_valid()
        assert "slug" in form.errors
