from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from features.booking.booking_settings import BookingSettings
from features.booking.models import Master, MasterWorkingDay
from features.main.models import Service, ServiceCategory, ServiceConflictRule

from system.models import CatalogImportState


class Command(BaseCommand):
    help = "Load the fixture-first service catalog"
    STATE_KEY = "service_catalog"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.base_fixtures_path = settings.BASE_DIR / "system" / "fixtures" / "catalog"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--force", action="store_true", help="Sync even when catalog fixture hash is unchanged")

    def handle(self, *args: Any, **options: Any) -> None:
        if not self.base_fixtures_path.exists():
            raise CommandError(f"Catalog fixtures directory not found: {self.base_fixtures_path}")

        source_hash = self._catalog_source_hash()
        state = CatalogImportState.objects.filter(key=self.STATE_KEY).first()
        if state and state.source_hash == source_hash and not options["force"]:
            self.stdout.write(self.style.SUCCESS("Catalog fixtures unchanged. Skipping database synchronization."))
            return

        self.stdout.write("Starting fixture-first catalog import...")
        with transaction.atomic():
            category_ids = self._sync_categories()
            service_ids = self._sync_services()
            master_ids = self._sync_masters()
            self._sync_working_days()
            self._sync_booking_settings()
            self._sync_service_master_links()
            self._sync_conflict_rules()
            self._deactivate_orphans(category_ids=category_ids, service_ids=service_ids, master_ids=master_ids)
            CatalogImportState.objects.update_or_create(
                key=self.STATE_KEY,
                defaults={"source_hash": source_hash},
            )

        self.stdout.write(self.style.SUCCESS("Catalog synchronized successfully."))

    def _fixture_path(self, *parts: str) -> Path:
        return self.base_fixtures_path.joinpath(*parts)

    def _catalog_source_hash(self) -> str:
        files = [
            self._fixture_path("categories.json"),
            self._fixture_path("masters.json"),
            self._fixture_path("working_days.json"),
            self._fixture_path("booking_settings.json"),
        ]
        services_dir = self._fixture_path("service")
        if not services_dir.is_dir():
            raise CommandError(f"Modular services directory not found: {services_dir}")
        files.extend(sorted(services_dir.glob("*.json")))

        conflict_rules_dir = self._fixture_path("conflict_rules")
        if conflict_rules_dir.is_dir():
            files.extend(sorted(conflict_rules_dir.glob("*.json")))
        else:
            files.append(self._fixture_path("conflict_rules.json"))

        digest = hashlib.sha256()
        for path in files:
            relative_path = path.relative_to(self.base_fixtures_path).as_posix()
            digest.update(relative_path.encode("utf-8"))
            digest.update(b"\0")
            if path.exists():
                digest.update(path.read_bytes())
            else:
                digest.update(b"<missing>")
            digest.update(b"\0")
        return digest.hexdigest()

    def _load_fixture(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"Fixture not found, skipped: {path}"))
            return []
        with path.open(encoding="utf-8") as fixture_file:
            return json.load(fixture_file)

    def _sync_categories(self) -> set[int]:
        processed_ids: set[int] = set()
        self.stdout.write("Syncing categories...")
        for item in self._load_fixture(self._fixture_path("categories.json")):
            pk = int(item["pk"])
            fields = dict(item["fields"])
            ServiceCategory.objects.update_or_create(pk=pk, defaults=fields)
            processed_ids.add(pk)
        return processed_ids

    def _sync_services(self) -> set[int]:
        processed_ids: set[int] = set()
        services_dir = self._fixture_path("service")
        if not services_dir.is_dir():
            raise CommandError(f"Modular services directory not found: {services_dir}")

        self.stdout.write("Syncing modular services...")
        for path in sorted(services_dir.glob("*.json")):
            for item in self._load_fixture(path):
                pk = int(item["pk"])
                fields = dict(item["fields"])
                excludes = fields.pop("excludes", [])
                category_id = fields.pop("category")

                service, _created = Service.objects.update_or_create(
                    pk=pk,
                    defaults={**fields, "category_id": category_id},
                )
                if excludes:
                    service.excludes.set(Service.objects.filter(pk__in=excludes))
                else:
                    service.excludes.clear()
                processed_ids.add(service.pk)
        return processed_ids

    def _sync_masters(self) -> set[int]:
        processed_ids: set[int] = set()
        self.stdout.write("Syncing masters...")
        for item in self._load_fixture(self._fixture_path("masters.json")):
            pk = int(item["pk"])
            fields = dict(item["fields"])
            categories = fields.pop("categories", [])

            master, _created = Master.objects.update_or_create(pk=pk, defaults=fields)
            master.categories.set(ServiceCategory.objects.filter(pk__in=categories))
            processed_ids.add(master.pk)
        return processed_ids

    def _sync_working_days(self) -> None:
        processed_ids: set[int] = set()
        self.stdout.write("Syncing working days...")
        for item in self._load_fixture(self._fixture_path("working_days.json")):
            pk = int(item["pk"])
            fields = dict(item["fields"])
            master_id = fields.pop("master")
            MasterWorkingDay.objects.update_or_create(pk=pk, defaults={**fields, "master_id": master_id})
            processed_ids.add(pk)

        if processed_ids:
            MasterWorkingDay.objects.exclude(pk__in=processed_ids).delete()

    def _sync_booking_settings(self) -> None:
        self.stdout.write("Syncing booking settings...")
        for item in self._load_fixture(self._fixture_path("booking_settings.json")):
            BookingSettings.objects.update_or_create(pk=int(item["pk"]), defaults=dict(item["fields"]))

    def _sync_service_master_links(self) -> None:
        self.stdout.write("Syncing service/master links...")
        active_masters = Master.objects.filter(status=Master.STATUS_ACTIVE).prefetch_related("categories")
        masters_by_category: dict[int, list[Master]] = {}
        for master in active_masters:
            for category_id in master.categories.values_list("pk", flat=True):
                masters_by_category.setdefault(category_id, []).append(master)

        for service in Service.objects.filter(is_active=True).select_related("category"):
            service.masters.set(masters_by_category.get(service.category_id, []))

    def _load_conflict_rule_items(self) -> list[dict[str, Any]]:
        conflict_rules_dir = self._fixture_path("conflict_rules")
        if conflict_rules_dir.is_dir():
            items: list[dict[str, Any]] = []
            for path in sorted(conflict_rules_dir.glob("*.json")):
                items.extend(self._load_fixture(path))
            return items
        return self._load_fixture(self._fixture_path("conflict_rules.json"))

    def _sync_conflict_rules(self) -> None:
        processed_ids: set[int] = set()
        self.stdout.write("Syncing conflict rules...")
        for item in self._load_conflict_rule_items():
            pk = int(item["pk"])
            fields = dict(item["fields"])
            ServiceConflictRule.objects.update_or_create(
                pk=pk,
                defaults={
                    "source_id": fields["source"],
                    "target_id": fields["target"],
                    "rule_type": fields["rule_type"],
                    "is_active": fields.get("is_active", True),
                    "note": fields.get("note", ""),
                },
            )
            processed_ids.add(pk)

        if processed_ids:
            ServiceConflictRule.objects.exclude(pk__in=processed_ids).delete()

    def _deactivate_orphans(self, *, category_ids: set[int], service_ids: set[int], master_ids: set[int]) -> None:
        inactive_services = Service.objects.exclude(pk__in=service_ids).filter(is_active=True).update(is_active=False)
        inactive_categories = (
            ServiceCategory.objects.exclude(pk__in=category_ids).filter(is_active=True).update(is_active=False)
        )
        inactive_masters = (
            Master.objects.exclude(pk__in=master_ids)
            .filter(status=Master.STATUS_ACTIVE)
            .update(status=Master.STATUS_INACTIVE)
        )

        if inactive_services:
            self.stdout.write(self.style.WARNING(f"Deactivated {inactive_services} services not present in fixtures."))
        if inactive_categories:
            self.stdout.write(
                self.style.WARNING(f"Deactivated {inactive_categories} categories not present in fixtures.")
            )
        if inactive_masters:
            self.stdout.write(self.style.WARNING(f"Deactivated {inactive_masters} masters not present in fixtures."))
