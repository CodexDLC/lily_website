"""Convert old backend booking/main fixtures → new lily_backend fixtures.

Run from src/lily_backend/:
    python ../../tools/make_booking_fixtures.py

Outputs:
    features/booking/fixtures/initial_categories.json
    features/booking/fixtures/initial_services.json
    features/booking/fixtures/initial_master.json
"""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent / "src"
OLD = ROOT / "backend_django"
NEW = ROOT / "lily_backend"

TIMESTAMP = "2024-01-01T00:00:00Z"


# ── 1. Categories ─────────────────────────────────────────────────────────────


def make_categories() -> list[dict]:
    src = OLD / "features/main/fixtures/initial_categories.json"
    with open(src, encoding="utf-8") as f:
        old = json.load(f)

    out = []
    for rec in old:
        f = rec["fields"]
        out.append(
            {
                "model": "booking.servicecategory",
                "pk": rec["pk"],
                "fields": {
                    "name": f.get("title_de") or f.get("title_en") or "",
                    "name_de": f.get("title_de") or "",
                    "name_ru": f.get("title_ru") or "",
                    "name_uk": f.get("title_uk") or "",
                    "name_en": f.get("title_en") or "",
                    "slug": f["slug"],
                    "bento_group": f.get("bento_group") or "",
                    "image": f.get("image") or "",
                    "icon": "",
                    "description": f.get("description_de") or "",
                    "content": f.get("content_de") or "",
                    "is_planned": f.get("is_planned", False),
                    "order": f.get("order", 0),
                },
            }
        )
    return out


# ── 2. Services ───────────────────────────────────────────────────────────────

SERVICE_FILES = [
    ("services_hair.json", 1),  # hair category pk=1
    ("services_nails.json", 2),
    ("services_brows_lashes.json", 3),
    ("services_cosmetology.json", 4),
    ("services_massage.json", 5),
    ("services_depilation.json", 6),
]


def make_services() -> list[dict]:
    base = OLD / "features/system/fixtures/content/service"
    out = []
    pk = 1
    for fname, cat_pk in SERVICE_FILES:
        fpath = base / fname
        if not fpath.exists():
            print(f"  SKIP {fname} — not found")
            continue
        with open(fpath, encoding="utf-8") as f:
            records = json.load(f)
        for rec in records:
            fields = rec["fields"]
            out.append(
                {
                    "model": "booking.service",
                    "pk": pk,
                    "fields": {
                        "name": fields.get("title_de") or fields.get("title", "") or "",
                        "name_de": fields.get("title_de") or "",
                        "name_ru": fields.get("title_ru") or "",
                        "name_uk": fields.get("title_uk") or "",
                        "name_en": fields.get("title_en") or "",
                        "slug": fields.get("slug") or "",
                        "category": cat_pk,
                        "price": str(fields.get("price") or "0.00"),
                        "price_info": fields.get("price_info_en") or fields.get("price_info_de") or "",
                        "duration": int(fields.get("duration") or 60),
                        "duration_info": fields.get("duration_info_de") or fields.get("duration_info") or "",
                        "description": fields.get("description_de") or fields.get("description") or "",
                        "content": fields.get("content_de") or fields.get("content") or "",
                        "image": fields.get("image") or "",
                        "is_active": fields.get("is_active", True),
                        "is_hit": fields.get("is_hit", False),
                        "is_addon": False,
                        "order": int(fields.get("order") or 0),
                    },
                }
            )
            pk += 1
    return out


# ── 3. Master (Lily) ──────────────────────────────────────────────────────────


def make_master() -> list[dict]:
    src = OLD / "features/booking/fixtures/initial_owner.json"
    with open(src, encoding="utf-8") as f:
        old = json.load(f)

    f = old[0]["fields"]
    return [
        {
            "model": "booking.master",
            "pk": 1,
            "fields": {
                "user": None,
                "name": f.get("name") or "Liliia Yakina",
                "title": f.get("title_de") or "",
                "title_de": f.get("title_de") or "",
                "title_ru": f.get("title_ru") or "",
                "title_uk": f.get("title_uk") or "",
                "title_en": f.get("title_en") or "",
                "slug": f.get("slug") or "liliia-yakina",
                "photo": f.get("photo") or "",
                "bio": f.get("bio_de") or "",
                "bio_de": f.get("bio_de") or "",
                "bio_ru": f.get("bio_ru") or "",
                "bio_uk": f.get("bio_uk") or "",
                "bio_en": f.get("bio_en") or "",
                "short_description": f.get("short_description_de") or "",
                "short_description_de": f.get("short_description_de") or "",
                "short_description_ru": f.get("short_description_ru") or "",
                "short_description_uk": f.get("short_description_uk") or "",
                "short_description_en": f.get("short_description_en") or "",
                "years_experience": int(f.get("years_experience") or 0),
                "instagram": f.get("instagram") or "",
                "phone": f.get("phone") or "",
                "status": "active",
                "is_owner": True,
                "is_featured": True,
                "is_public": True,
                "order": 0,
                "telegram_id": None,
                "telegram_username": "",
                "bot_access_code": None,
                "qr_token": None,
            },
        }
    ]


# ── Main ──────────────────────────────────────────────────────────────────────


def write(path: Path, data: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ {path.relative_to(NEW)} — {len(data)} records")


if __name__ == "__main__":
    os.chdir(NEW)
    print("── Categories ──")
    cats = make_categories()
    write(NEW / "features/booking/fixtures/initial_categories.json", cats)

    print("── Services ──")
    svcs = make_services()
    write(NEW / "features/booking/fixtures/initial_services.json", svcs)

    print("── Master ──")
    master = make_master()
    write(NEW / "features/booking/fixtures/initial_master.json", master)

    print(f"\nDone. Categories: {len(cats)}, Services: {len(svcs)}, Masters: {len(master)}")
