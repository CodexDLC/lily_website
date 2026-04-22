from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import psycopg2
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from psycopg2.extras import RealDictCursor

LANG_FIELDS = ("text", "text_de", "text_ru", "text_uk", "text_en")
DEFAULT_FIXTURE_PATH = settings.BASE_DIR / "system" / "fixtures" / "content" / "email_content.json"


class Command(BaseCommand):
    help = "Export EmailContent rows from legacy PostgreSQL as JSON fixture entries."

    def add_arguments(self, parser):
        parser.add_argument("--url", type=str, help="Legacy PostgreSQL connection URL")
        parser.add_argument(
            "--env",
            type=str,
            default="LEGACY_DATABASE_URL",
            help="Environment variable with the legacy PostgreSQL connection URL",
        )
        parser.add_argument(
            "--table",
            type=str,
            default="system_emailcontent",
            help="Legacy EmailContent table name",
        )
        parser.add_argument(
            "--prefix",
            action="append",
            default=[],
            help="Only export keys with this prefix. Can be passed multiple times.",
        )
        parser.add_argument(
            "--key",
            action="append",
            default=[],
            help="Only export this exact key. Can be passed multiple times.",
        )
        parser.add_argument(
            "--fixture",
            type=Path,
            default=DEFAULT_FIXTURE_PATH,
            help="Current fixture path used for merge mode",
        )
        parser.add_argument(
            "--merge",
            action="store_true",
            help="Merge exported rows with the current fixture by EmailContent key",
        )
        parser.add_argument(
            "--output",
            type=Path,
            help="Write result to this JSON file instead of stdout",
        )
        parser.add_argument(
            "--write-fixture",
            action="store_true",
            help="Write merged result back to --fixture. Requires --merge.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        db_url = options["url"] or os.environ.get(options["env"])
        if not db_url:
            raise CommandError(f"Must provide --url or set {options['env']} env var")

        if options["write_fixture"] and not options["merge"]:
            raise CommandError("--write-fixture requires --merge")

        rows = self._fetch_rows(
            db_url=db_url,
            table=options["table"],
            prefixes=tuple(options["prefix"]),
            keys=tuple(options["key"]),
        )
        entries = [_row_to_fixture_entry(row) for row in rows]

        result = _merge_fixture_entries(_load_fixture(options["fixture"]), entries) if options["merge"] else entries

        output_path: Path | None = options["output"]
        if options["write_fixture"]:
            output_path = options["fixture"]

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(_format_fixture(result), encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Wrote {len(result)} EmailContent rows to {output_path}"))
            return

        self.stdout.write(_format_fixture(result))

    def _fetch_rows(
        self,
        *,
        db_url: str,
        table: str,
        prefixes: tuple[str, ...],
        keys: tuple[str, ...],
    ) -> list[dict[str, Any]]:
        query, params = _build_query(table=table, prefixes=prefixes, keys=keys)
        self.stdout.write(f"Reading EmailContent rows from legacy table '{table}'...")

        try:
            with psycopg2.connect(db_url, cursor_factory=RealDictCursor) as conn:
                conn.set_session(readonly=True, autocommit=True)
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    rows = [dict(row) for row in cursor.fetchall()]
        except Exception as exc:
            raise CommandError(f"Could not read legacy EmailContent rows: {exc}") from exc

        self.stdout.write(f"Found {len(rows)} EmailContent rows.")
        return rows


def _build_query(*, table: str, prefixes: tuple[str, ...], keys: tuple[str, ...]) -> tuple[str, list[str]]:
    if not table.replace("_", "").isalnum():
        raise CommandError(f"Unsafe table name: {table!r}")

    clauses: list[str] = []
    params: list[str] = []

    if prefixes:
        clauses.append("(" + " OR ".join(["key LIKE %s"] * len(prefixes)) + ")")
        params.extend(f"{prefix}%" for prefix in prefixes)

    if keys:
        clauses.append("key = ANY(%s)")
        params.append(list(keys))  # type: ignore[arg-type]

    where_sql = f" WHERE {' OR '.join(clauses)}" if clauses else ""
    return f"SELECT * FROM {table}{where_sql} ORDER BY key", params  # nosec B608


def _row_to_fixture_entry(row: dict[str, Any]) -> dict[str, Any]:
    key = str(row.get("key") or "").strip()
    if not key:
        raise CommandError("Legacy EmailContent row without key")

    fields: dict[str, Any] = {
        "key": key,
        "category": row.get("category") or _infer_category(key),
        "description": row.get("description") or "",
    }

    for field in LANG_FIELDS:
        fields[field] = row.get(field) or ""

    if not fields["text"]:
        fields["text"] = fields["text_de"] or fields["text_en"] or fields["text_ru"] or fields["text_uk"]

    return {
        "model": "system.emailcontent",
        "fields": fields,
    }


def _infer_category(key: str) -> str:
    if key.startswith("bk_"):
        return "booking"
    if key.startswith("ct_"):
        return "contacts"
    if key.startswith("acc_") or key.startswith("pwd_"):
        return "account"
    if key.startswith("mk_"):
        return "marketing"
    return "general"


def _load_fixture(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise CommandError(f"Fixture not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _merge_fixture_entries(
    current_entries: list[dict[str, Any]],
    exported_entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged_by_key: dict[str, dict[str, Any]] = {}
    current_order: list[str] = []

    for entry in current_entries:
        key = entry.get("fields", {}).get("key")
        if key:
            normalized_key = str(key)
            current_order.append(normalized_key)
            merged_by_key[normalized_key] = entry

    for entry in exported_entries:
        key = entry["fields"]["key"]
        existing = merged_by_key.get(key)
        if existing is None:
            merged_by_key[key] = entry
            continue

        existing_fields = existing.setdefault("fields", {})
        exported_fields = entry["fields"]
        for field in ("category", "description", *LANG_FIELDS):
            if not existing_fields.get(field) and exported_fields.get(field):
                existing_fields[field] = exported_fields[field]

    current_keys = set(current_order)
    new_keys = sorted(key for key in merged_by_key if key not in current_keys)
    return [merged_by_key[key] for key in [*current_order, *new_keys]]


def _format_fixture(entries: list[dict[str, Any]]) -> str:
    return json.dumps(entries, ensure_ascii=False, indent=2) + "\n"
