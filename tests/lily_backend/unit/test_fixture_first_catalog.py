from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import call, patch

import pytest
from django.core.management import call_command
from django.test import RequestFactory, override_settings
from django.utils import timezone


def _write_json(path: Path, data: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _write_minimal_catalog(fixtures_dir: Path, *, service_name: str) -> None:
    _write_json(
        fixtures_dir / "categories.json",
        [
            {
                "model": "main.servicecategory",
                "pk": 9100,
                "fields": {"name": "Hash Category", "slug": "hash-category", "is_active": True},
            }
        ],
    )
    _write_json(
        fixtures_dir / "service" / "services_hash.json",
        [
            {
                "model": "main.service",
                "pk": 9200,
                "fields": {
                    "name": service_name,
                    "slug": "hash-service",
                    "category": 9100,
                    "price": "25.00",
                    "duration": 45,
                    "is_active": True,
                    "excludes": [],
                },
            }
        ],
    )
    _write_json(fixtures_dir / "masters.json", [])
    _write_json(fixtures_dir / "working_days.json", [])
    _write_json(fixtures_dir / "booking_settings.json", [])
    _write_json(fixtures_dir / "conflict_rules.json", [])


@pytest.mark.unit
def test_load_catalog_uses_modular_services_and_deactivates_orphans(tmp_path, category):
    from features.booking.models import Master
    from features.main.models import Service, ServiceCategory

    fixtures_dir = tmp_path / "system" / "fixtures" / "catalog"
    services_dir = fixtures_dir / "service"

    orphan = Service.objects.create(
        category=category,
        name="Legacy Service",
        slug="legacy-service",
        price="10.00",
        duration=30,
        is_active=True,
    )

    _write_json(
        fixtures_dir / "categories.json",
        [
            {
                "model": "main.servicecategory",
                "pk": 100,
                "fields": {"name": "Fixture Category", "slug": "fixture-category", "is_active": True},
            }
        ],
    )
    _write_json(
        services_dir / "services_fixture.json",
        [
            {
                "model": "main.service",
                "pk": 200,
                "fields": {
                    "name": "Fixture Service",
                    "slug": "fixture-service",
                    "category": 100,
                    "price": "25.00",
                    "duration": 45,
                    "is_active": True,
                    "excludes": [],
                },
            }
        ],
    )
    _write_json(
        fixtures_dir / "services.json",
        [
            {
                "model": "main.service",
                "pk": 201,
                "fields": {
                    "name": "Ignored Flat Service",
                    "slug": "ignored-flat-service",
                    "category": 100,
                    "price": "99.00",
                    "duration": 90,
                    "is_active": True,
                },
            }
        ],
    )
    _write_json(
        fixtures_dir / "masters.json",
        [
            {
                "model": "booking.master",
                "pk": 300,
                "fields": {
                    "name": "Fixture Master",
                    "slug": "fixture-master",
                    "status": "active",
                    "is_public": True,
                    "categories": [100],
                },
            }
        ],
    )
    _write_json(
        fixtures_dir / "working_days.json",
        [
            {
                "model": "booking.masterworkingday",
                "pk": 400,
                "fields": {
                    "master": 300,
                    "weekday": 0,
                    "start_time": "09:00:00",
                    "end_time": "18:00:00",
                    "break_start": None,
                    "break_end": None,
                },
            }
        ],
    )
    _write_json(fixtures_dir / "booking_settings.json", [])
    _write_json(fixtures_dir / "conflict_rules.json", [])

    with override_settings(BASE_DIR=tmp_path):
        call_command("load_catalog")

    fixture_service = Service.objects.get(pk=200)
    assert fixture_service.is_active is True
    assert fixture_service.masters.filter(pk=300).exists()
    assert not Service.objects.filter(slug="ignored-flat-service").exists()

    orphan.refresh_from_db()
    assert orphan.is_active is False
    assert ServiceCategory.objects.get(pk=100).is_active is True
    assert Master.objects.get(pk=300).status == Master.STATUS_ACTIVE


@pytest.mark.unit
def test_load_catalog_skips_database_sync_when_fixture_hash_is_unchanged(tmp_path):
    from features.main.models import Service
    from system.models import CatalogImportState

    fixtures_dir = tmp_path / "system" / "fixtures" / "catalog"
    _write_minimal_catalog(fixtures_dir, service_name="Fixture Service")

    with override_settings(BASE_DIR=tmp_path):
        call_command("load_catalog")

    state = CatalogImportState.objects.get(key="service_catalog")
    first_hash = state.source_hash

    Service.objects.filter(pk=9200).update(name="Manual Database Edit")

    with override_settings(BASE_DIR=tmp_path):
        call_command("load_catalog")

    assert Service.objects.get(pk=9200).name == "Manual Database Edit"
    state.refresh_from_db()
    assert state.source_hash == first_hash

    _write_minimal_catalog(fixtures_dir, service_name="Changed Fixture Service")

    with override_settings(BASE_DIR=tmp_path):
        call_command("load_catalog")

    assert Service.objects.get(pk=9200).name == "Changed Fixture Service"
    state.refresh_from_db()
    assert state.source_hash != first_hash


@pytest.mark.unit
def test_load_catalog_loads_repository_fixtures():
    from features.booking.models import Master
    from features.main.models import Service, ServiceConflictRule

    call_command("load_catalog")

    assert Service.objects.filter(is_active=True).count() > 0
    assert Master.objects.filter(status=Master.STATUS_ACTIVE).count() > 0
    assert Service.objects.filter(is_active=True, masters__isnull=False).exists()
    assert ServiceConflictRule.objects.exists()


@pytest.mark.unit
def test_migrate_all_legacy_runs_only_operational_imports():
    with patch("system.management.commands.migrate_all_legacy.call_command") as mocked_call_command:
        call_command("migrate_all_legacy", url="postgres://legacy.example/db", dry_run=True)

    assert mocked_call_command.call_args_list == [
        call("migrate_users", url="postgres://legacy.example/db", dry_run=True),
        call("migrate_clients", url="postgres://legacy.example/db", dry_run=True),
        call("migrate_appointments", url="postgres://legacy.example/db", dry_run=True),
    ]


class _LegacyCursor:
    def __init__(self, query_results: dict[str, list[dict]]) -> None:
        self.query_results = query_results
        self.current_query = ""

    def execute(self, query: str) -> None:
        self.current_query = query

    def fetchall(self) -> list[dict]:
        for key, rows in self.query_results.items():
            if key in self.current_query:
                return rows
        return []


class _LegacyConnection:
    def __init__(self, cursor: _LegacyCursor) -> None:
        self._cursor = cursor

    def cursor(self) -> _LegacyCursor:
        return self._cursor

    def close(self) -> None:
        pass


@pytest.mark.unit
def test_migrate_clients_preserves_legacy_timestamps():
    from system.models import Client

    legacy_created = timezone.make_aware(timezone.datetime(2024, 2, 10, 9, 30))
    legacy_updated = timezone.make_aware(timezone.datetime(2024, 3, 11, 10, 45))
    cursor = _LegacyCursor(
        {
            "booking_client": [
                {
                    "id": 501,
                    "phone": "+49177000111",
                    "email": "legacy-client@example.test",
                    "first_name": "Legacy",
                    "last_name": "Client",
                    "notes": "",
                    "status": "guest",
                    "user_id": None,
                    "created_at": legacy_created,
                    "updated_at": legacy_updated,
                }
            ]
        }
    )

    with patch("psycopg2.connect", return_value=_LegacyConnection(cursor)):
        call_command("migrate_clients", url="postgres://legacy.example/db")

    client = Client.objects.get(phone="+49177000111")
    assert client.created_at == legacy_created
    assert client.updated_at == legacy_updated


@pytest.mark.unit
def test_migrate_appointments_updates_existing_legacy_timestamps(client_obj, master, service):
    from features.booking.models import Appointment

    legacy_start = timezone.make_aware(timezone.datetime(2024, 4, 12, 14, 0))
    legacy_created = timezone.make_aware(timezone.datetime(2024, 1, 5, 8, 15))
    legacy_updated = timezone.make_aware(timezone.datetime(2024, 1, 6, 9, 45))
    existing = Appointment.objects.create(
        client=client_obj,
        master=master,
        service=service,
        datetime_start=legacy_start,
        duration_minutes=service.duration,
        price=service.price,
        status=Appointment.STATUS_PENDING,
    )

    cursor = _LegacyCursor(
        {
            "booking_appointment": [
                {
                    "id": 701,
                    "client_id": 501,
                    "master_id": 601,
                    "service_id": 801,
                    "datetime_start": legacy_start,
                    "duration_minutes": service.duration,
                    "status": existing.status,
                    "price": service.price,
                    "created_at": legacy_created,
                    "updated_at": legacy_updated,
                }
            ],
            "booking_master": [{"id": 601, "name": master.name}],
            "main_service": [{"id": 801, "title": service.name}],
            "booking_client": [{"id": 501, "phone": client_obj.phone, "email": client_obj.email}],
        }
    )

    with patch("psycopg2.connect", return_value=_LegacyConnection(cursor)):
        call_command("migrate_appointments", url="postgres://legacy.example/db")

    existing.refresh_from_db()
    assert existing.created_at == legacy_created
    assert existing.updated_at == legacy_updated


@pytest.mark.unit
@override_settings(DEBUG=True)
def test_data_maintenance_migrate_all_uses_operational_import():
    from src.lily_backend.cabinet.views.ops import DataMaintenanceView

    request = RequestFactory().post("/cabinet/ops/maintenance/", {"action": "migrate_all"})
    request.session = {}

    with (
        patch("src.lily_backend.cabinet.views.ops.call_command") as mocked_call_command,
        patch("src.lily_backend.cabinet.views.ops.redirect") as mocked_redirect,
    ):
        DataMaintenanceView().post(request)

    mocked_call_command.assert_called_once()
    assert mocked_call_command.call_args.args[0] == "migrate_all_legacy"
    mocked_redirect.assert_called_once_with("cabinet:ops_maintenance")


@pytest.mark.unit
def test_data_maintenance_streams_command_output_to_console(capsys):
    from src.lily_backend.cabinet.views.ops import DataMaintenanceView

    request = RequestFactory().post("/cabinet/ops/maintenance/", {"action": "sync_catalog"})
    request.session = {}

    def fake_call_command(*args, **kwargs):
        kwargs["stdout"].write("stdout line\n")
        kwargs["stderr"].write("stderr line\n")

    with (
        patch("src.lily_backend.cabinet.views.ops.call_command", side_effect=fake_call_command),
        patch("src.lily_backend.cabinet.views.ops.redirect"),
    ):
        DataMaintenanceView().post(request)

    captured = capsys.readouterr()

    assert "stdout line" in captured.out
    assert "stderr line" in captured.err
    assert "stdout line" in request.session["maintenance_log"]
    assert "stderr line" in request.session["maintenance_log"]


@pytest.mark.unit
def test_current_backend_entrypoint_runs_startup_commands_before_gunicorn():
    content = Path("deploy/lily_backend/entrypoint.sh").read_text(encoding="utf-8")

    assert Path("deploy/backend/entrypoint.sh").exists() is False
    assert 'if [ "$#" -gt 0 ]; then' in content
    assert 'exec "$@"' in content
    assert "python /app/manage.py collectstatic --noinput" in content
    assert "python /app/manage.py migrate --noinput" in content
    assert "python /app/manage.py load_catalog" in content
    assert "python /app/manage.py update_all_content" in content
    assert 'if [ "$RUN_LEGACY_MIGRATION" = "true" ] && [ "$DEBUG" = "True" ]; then' in content
    assert "python /app/manage.py migrate_all_legacy" in content
    assert "exec gunicorn core.wsgi:application" in content
    assert content.index("collectstatic") < content.index("exec gunicorn")
    assert content.index("migrate --noinput") < content.index("exec gunicorn")
    assert content.index("load_catalog") < content.index("exec gunicorn")
    assert content.index("update_all_content") < content.index("exec gunicorn")
