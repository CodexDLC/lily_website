from datetime import datetime
from typing import Any, cast

import psycopg2
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from features.booking.models import Appointment, Master
from features.main.models import Service
from psycopg2.extras import RealDictCursor

from system.models import Client


def _row_get(row: Any, key: str, default: Any = None) -> Any:
    if hasattr(row, "get"):
        return row.get(key, default)
    try:
        return row[key]
    except (IndexError, KeyError):
        return default


def _coerce_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, str):
        value = parse_datetime(value)
    if not isinstance(value, datetime):
        return None
    return timezone.make_aware(value) if timezone.is_naive(value) else value


class Command(BaseCommand):
    help = "Migrate appointments from legacy PostgreSQL database"

    # Remove hardcoded mappings that force all appointments to Liliia Yakina.
    # The migrate_masters script imports the exact names (like 'Лилия', 'Cosmetolog').
    MASTER_MAPPING: dict[str, str] = {}

    SERVICE_MAPPING = {
        "Maniküre + Gellack (Premium)": "Manicure + Gel Polish (Premium)",
        "Smart-Pediküre Komplett": "Smart Pedicure Complete",
        "Wimpernverlängerung 2D-3D": "Eyelash Extensions 2D-3D",
        "Wimpernlaminierung": "Lash Lamination",
        "Wimpern- und Augenbrauen-Komplex": "Complex: Lashes + Brows",
        "Klassische Massage (Ganzkörper)": "Classic Massage (Full Body)",
        "Kombinierte Gesichtsreinigung": "Combined Facial Cleansing",
        "Nagelverlängerungen (bis zu 3 cm)": "Nail Extensions (up to 3 cm)",
        "Augenbrauenlaminierung (Brow Lift)": "Brow Lamination",
        "Classic 1D": "Classic 1D Extensions",
        "Klassik 1D": "Classic 1D Extensions",
        "Pediküre (nur Zehen) mit UV-Lack": "Smart Pedicure Complete",
        "Korrektur (bis 2 Wochen)": "Lash Correction (up to 2 weeks)",
        "SMART-Pediküre (ohне Lack)": "Smart Pedicure Complete",
        "SMART-Pediküre (ohne Lack)": "Smart Pedicure Complete",
        "Klassische Damenmaniküre": "Classic Women's Manicure",
        "Oberlippe": "Upper Lip",
        "HydraFacial (Hollywood Glow)": "HydraFacial (Hollywood Glow)",
        "Maniküre + normaler Nagellack": "Manicure + Regular Polish",
        "Педикюр (только пальчики)": "Smart Pedicure Complete",
        "Anti-Cellulite Massage (Beine & Po)": "Anti-Cellulite (Legs & Glutes)",
    }

    def add_arguments(self, parser):
        parser.add_argument("--url", type=str, help="PostgreSQL connection URL")
        parser.add_argument("--dry-run", action="store_true", help="Do not save changes")
        parser.add_argument("--wipe", action="store_true", help="Delete all existing appointments before re-migrating")

    def handle(self, *args, **options):
        import os

        db_url = options["url"] or os.environ.get("LEGACY_DATABASE_URL")
        if not db_url:
            self.stdout.write(self.style.ERROR("Must provide --url (postgres) or set LEGACY_DATABASE_URL env var"))
            return
        self.stdout.write(f"Connecting to PostgreSQL: {db_url[:30]}...")

        try:
            conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
            cursor = conn.cursor()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Connection failed: {e}"))
            return

        try:
            cursor.execute("SELECT * FROM booking_appointment")
            legacy_apps = cursor.fetchall()

            cursor.execute("SELECT id, name FROM booking_master")
            legacy_masters = {row["id"]: row["name"] for row in cursor.fetchall()}

            cursor.execute("SELECT id, title FROM main_service")
            legacy_services = {row["id"]: row["title"] for row in cursor.fetchall()}

            cursor.execute("SELECT id, phone, email FROM booking_client")
            legacy_clients = {row["id"]: (row["phone"], row["email"]) for row in cursor.fetchall()}

            # Build lookup maps using ALL language variants to survive mixed-language legacy data.
            masters_obj_map: dict[str, Master] = {}
            for m in Master.objects.all():
                for field in ("name", "name_de", "name_en", "name_ru", "name_uk"):
                    val = getattr(m, field, None)
                    if val:
                        masters_obj_map[val.strip().lower()] = m

            services_obj_map: dict[str, Service] = {}
            for s in Service.objects.all():
                for field in ("name", "name_de", "name_en", "name_ru", "name_uk"):
                    val = getattr(s, field, None)
                    if val:
                        services_obj_map[val.strip().lower()] = s

            if options.get("wipe") and not options["dry_run"]:
                deleted, _ = Appointment.objects.all().delete()
                self.stdout.write(self.style.WARNING(f"Wiped {deleted} existing appointments."))

            created_count = 0
            updated_count = 0
            skipped_count = 0

            for row in legacy_apps:
                phone, email = legacy_clients.get(_row_get(row, "client_id"), (None, None))
                client = Client.objects.filter(phone=phone).first() if phone else None
                if not client and email:
                    client = Client.objects.filter(email=email).first()

                if not client:
                    skipped_count += 1
                    continue

                legacy_m_name = legacy_masters.get(_row_get(row, "master_id"))
                new_m_name = (
                    self.MASTER_MAPPING.get(cast("str", legacy_m_name), legacy_m_name) if legacy_m_name else None
                )
                # Try mapped name first, then original name (case-insensitive)
                master = None
                if new_m_name:
                    master = masters_obj_map.get(new_m_name.strip().lower())
                if not master and legacy_m_name:
                    master = masters_obj_map.get(cast("str", legacy_m_name).strip().lower())
                if not master:
                    self.stdout.write(self.style.WARNING(f"  Skipping: master '{legacy_m_name}' not found"))
                    skipped_count += 1
                    continue

                legacy_s_name = legacy_services.get(_row_get(row, "service_id"))
                new_s_name = (
                    self.SERVICE_MAPPING.get(cast("str", legacy_s_name), legacy_s_name) if legacy_s_name else None
                )
                # Try mapped name first, then original name (case-insensitive)
                service = None
                if new_s_name:
                    service = services_obj_map.get(new_s_name.strip().lower())
                if not service and legacy_s_name:
                    service = services_obj_map.get(cast("str", legacy_s_name).strip().lower())
                if not service:
                    self.stdout.write(self.style.WARNING(f"  Skipping: service '{legacy_s_name}' not found"))
                    skipped_count += 1
                    continue

                dt_start = _coerce_datetime(_row_get(row, "datetime_start"))

                duration = _row_get(row, "duration_minutes", 60)
                legacy_created_at = _coerce_datetime(_row_get(row, "created_at")) or dt_start
                legacy_updated_at = _coerce_datetime(_row_get(row, "updated_at")) or legacy_created_at

                # Check if this appointment already exists to avoid duplicates
                existing = Appointment.objects.filter(client=client, master=master, datetime_start=dt_start).first()

                if existing:
                    timestamp_updates = {}
                    if legacy_created_at:
                        timestamp_updates["created_at"] = legacy_created_at
                    if legacy_updated_at:
                        timestamp_updates["updated_at"] = legacy_updated_at
                    if timestamp_updates and not options["dry_run"]:
                        Appointment.objects.filter(pk=existing.pk).update(**timestamp_updates)
                    updated_count += 1
                    continue

                app = Appointment(
                    client=client,
                    master=master,
                    service=service,
                    datetime_start=dt_start,
                    duration_minutes=duration,
                    status=_row_get(row, "status", "scheduled"),
                    price=_row_get(row, "price", 0),
                )

                if not options["dry_run"]:
                    try:
                        with transaction.atomic():
                            app.save()
                        timestamp_updates = {
                            "created_at": legacy_created_at or dt_start or timezone.now(),
                            "updated_at": legacy_updated_at or legacy_created_at or dt_start or timezone.now(),
                        }
                        Appointment.objects.filter(id=app.id).update(**timestamp_updates)
                        created_count += 1
                    except Exception:
                        skipped_count += 1
                else:
                    created_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Migration complete. Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}"
                )
            )

        finally:
            conn.close()
