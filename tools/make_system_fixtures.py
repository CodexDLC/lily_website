"""
tools/make_system_fixtures.py
==============================================
Converts old-backend data sources into Django fixtures for the new lily_backend.

Sources (read from src/backend_django/):
  1. features/system/fixtures/seo/static_pages_seo.json        → system/fixtures/seo/static_pages_seo.json
  2. features/system/fixtures/initial_email_content.json        → system/fixtures/content/email_content.json
  3. features/system/fixtures/content/static_translations.py   → system/fixtures/content/static_translations.json

Usage:
    python tools/make_system_fixtures.py
"""

import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent
OLD = ROOT / "src" / "backend_django" / "features" / "system"
NEW = ROOT / "src" / "lily_backend" / "system" / "fixtures"

LANGS = ("de", "ru", "uk", "en")
TIMESTAMP = "2024-01-01T00:00:00Z"


# ─────────────────────────────────────────────────────────────────────────────
# 1. StaticPageSeo  (old format: plain dict  →  Django fixture)
# ─────────────────────────────────────────────────────────────────────────────


def convert_seo() -> list[dict]:
    src = OLD / "fixtures" / "seo" / "static_pages_seo.json"
    data: dict = json.loads(src.read_text(encoding="utf-8"))

    records = []
    pk = 1
    for page_key, fields in data.items():
        record: dict[str, Any] = {
            "model": "system.staticpageseo",
            "pk": pk,
            "fields": {
                "page_key": page_key,
                "seo_title": fields.get("seo_title_de", ""),
                "seo_description": fields.get("seo_description_de", ""),
                "created_at": TIMESTAMP,
                "updated_at": TIMESTAMP,
            },
        }
        for lang in LANGS:
            record["fields"][f"seo_title_{lang}"] = fields.get(f"seo_title_{lang}", "")
            record["fields"][f"seo_description_{lang}"] = fields.get(f"seo_description_{lang}", "")
        records.append(record)
        pk += 1

    return records


# ─────────────────────────────────────────────────────────────────────────────
# 2. EmailContent  (old Django fixture, just rename model label)
# ─────────────────────────────────────────────────────────────────────────────


def convert_email_content() -> list[dict]:
    src = OLD / "fixtures" / "initial_email_content.json"
    old_records: list[dict] = json.loads(src.read_text(encoding="utf-8"))

    records = []
    pk = 1
    for item in old_records:
        fields = item["fields"]
        record: dict[str, Any] = {
            "model": "system.emailcontent",
            "pk": pk,
            "fields": {
                "key": fields["key"],
                "category": fields.get("category", "general"),
                "description": fields.get("description", ""),
                "text": fields.get("text_de", ""),
            },
        }
        for lang in LANGS:
            record["fields"][f"text_{lang}"] = fields.get(f"text_{lang}", "")
        records.append(record)
        pk += 1

    return records


# ─────────────────────────────────────────────────────────────────────────────
# 3. StaticTranslation  (old Python module  →  Django fixture)
# ─────────────────────────────────────────────────────────────────────────────


def convert_static_translations() -> list[dict]:
    # Load the Python module with DATA dict
    module_path = OLD / "fixtures" / "content" / "static_translations.py"
    spec = importlib.util.spec_from_file_location("static_translations", module_path)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    data: dict = mod.DATA

    records = []
    pk = 1
    for key, translations in data.items():
        record: dict[str, Any] = {
            "model": "system.statictranslation",
            "pk": pk,
            "fields": {
                "key": key,
                "content": translations.get("de", ""),
                "created_at": TIMESTAMP,
                "updated_at": TIMESTAMP,
            },
        }
        for lang in LANGS:
            record["fields"][f"content_{lang}"] = translations.get(lang, "")
        records.append(record)
        pk += 1

    return records


# ─────────────────────────────────────────────────────────────────────────────
# main
# ─────────────────────────────────────────────────────────────────────────────


def write(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Wrote {len(records):>4} records → {path.relative_to(ROOT)}")


if __name__ == "__main__":
    print("Converting system fixtures...")

    seo = convert_seo()
    write(NEW / "seo" / "static_pages_seo.json", seo)

    email = convert_email_content()
    write(NEW / "content" / "email_content.json", email)

    static = convert_static_translations()
    write(NEW / "content" / "static_translations.json", static)

    print("Done.")
