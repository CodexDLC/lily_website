"""
tools/migrate_locale.py

Split legacy monolithic django.po files into domain-organised locale structure.

Domain layout:
  locale/system/       — nav_*, btn_*, label_*, footer_*, msg_*, shared UI
  locale/main/         — service_cat_*, service_item_*
  locale/booking/      — cancellation_policy_*, booking-specific strings
  locale/conversations/ — contact-form strings

Usage:
    python tools/migrate_locale.py
    python tools/migrate_locale.py --dry-run   # print summary only

All four locales (de, en, ru, uk) are processed automatically.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
SRC_OLD = REPO_ROOT / "src" / "backend_django" / "locale"
SRC_NEW = REPO_ROOT / "src" / "lily_backend" / "locale"
LOCALES = ["de", "en", "ru", "uk"]
DOMAINS = ["system", "main", "booking", "conversations"]

# ---------------------------------------------------------------------------
# Domain routing — ordered, first match wins.
# Each rule: (domain, compiled regex matching against msgid)
# ---------------------------------------------------------------------------
RULES: list[tuple[str, re.Pattern[str]]] = [
    # main — service catalogue labels used in templates
    ("main", re.compile(r"^service_cat_")),
    ("main", re.compile(r"^service_item_")),
    # booking — cancellation flow & promo trigger
    ("booking", re.compile(r"^cancellation_policy_")),
    ("booking", re.compile(r"^btn_ui_show_promo")),
    ("booking", re.compile(r"^btn_ui_toggle_footer")),
    # conversations — (no prefix-based keys currently; reserved for future)
    # system — everything else (nav, btn, label, footer, msg, all verbose names)
]


def route(msgid: str) -> str:
    """Return the domain name for a given msgid."""
    for domain, pattern in RULES:
        if pattern.match(msgid):
            return domain
    return "system"


# ---------------------------------------------------------------------------
# Minimal PO parser — preserves comments, flags, and multiline strings.
# ---------------------------------------------------------------------------

Entry = list[str]  # raw lines belonging to one catalog entry (incl. blank)


def parse_po(path: Path) -> tuple[list[str], list[Entry]]:
    """Return (header_lines, entries).

    header_lines — everything before the first non-empty msgid entry.
    entries      — each entry is a list of raw lines (blank line included).
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    header_lines: list[str] = []
    entries: list[Entry] = []
    current: Entry = []
    in_header = True

    for line in lines:
        if in_header:
            current.append(line)
            # The header entry ends at the blank line after the first msgstr block
            if line.strip() == "" and any(line_content.startswith("msgstr") for line_content in current):
                header_lines = current[:]
                current = []
                in_header = False
            continue

        # Body entries
        if line.strip() == "":
            if current:
                entries.append(current[:])
                current = []
            # keep blank line as separator (will be re-emitted)
        else:
            current.append(line)

    if current:
        entries.append(current)

    return header_lines, entries


def extract_msgid(entry: Entry) -> str:
    """Extract the raw msgid string value from an entry."""
    # Collect msgid lines (may be multiline)
    collecting = False
    parts: list[str] = []
    for line in entry:
        if line.startswith("msgid "):
            raw = line[len("msgid ") :].strip()
            parts.append(raw.strip('"'))
            collecting = True
        elif collecting:
            stripped = line.strip()
            if stripped.startswith('"') and not line.startswith("msgstr"):
                parts.append(stripped.strip('"'))
            else:
                break
    return "".join(parts)


HEADER_TEMPLATE = """\
# LILY Beauty Salon — {domain} domain translations
# Language: {lang}
#
msgid ""
msgstr ""
"Project-Id-Version: lily_backend\\n"
"Report-Msgid-Bugs-To: \\n"
"Language-Team: {lang_team}\\n"
"Language: {lang}\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"

"""

LANG_TEAMS = {"de": "German", "en": "English", "ru": "Russian", "uk": "Ukrainian"}


def make_header(domain: str, lang: str) -> str:
    return HEADER_TEMPLATE.format(
        domain=domain,
        lang=lang,
        lang_team=LANG_TEAMS.get(lang, lang),
    )


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------


def migrate(dry_run: bool = False) -> None:
    stats: dict[str, dict[str, int]] = {lang: {d: 0 for d in DOMAINS} for lang in LOCALES}
    missing_source: list[str] = []

    for lang in LOCALES:
        src_po = SRC_OLD / lang / "LC_MESSAGES" / "django.po"

        if not src_po.exists():
            missing_source.append(str(src_po))
            print(f"  [SKIP] {lang}: source not found — {src_po}")
            continue

        header_lines, entries = parse_po(src_po)

        # Bucket entries by domain
        buckets: dict[str, list[Entry]] = {d: [] for d in DOMAINS}

        for entry in entries:
            msgid = extract_msgid(entry)
            if not msgid:  # empty msgid = header duplicate; skip
                continue
            domain = route(msgid)
            buckets[domain].append(entry)
            stats[lang][domain] += 1

        if dry_run:
            print(f"\n  {lang}:")
            for domain in DOMAINS:
                print(f"    {domain:20s} {stats[lang][domain]:4d} entries")
            continue

        # Write domain files
        for domain in DOMAINS:
            out_path = SRC_NEW / domain / lang / "LC_MESSAGES" / "django.po"
            out_path.parent.mkdir(parents=True, exist_ok=True)

            with out_path.open("w", encoding="utf-8", newline="\n") as fh:
                fh.write(make_header(domain, lang))
                for entry in buckets[domain]:
                    fh.writelines(entry)
                    fh.write("\n")

            print(f"  wrote {out_path} ({stats[lang][domain]} entries)")

    # Summary
    print("\n=== Summary ===")
    header = f"{'lang':>6}  " + "  ".join(f"{d:>16}" for d in DOMAINS)
    print(header)
    for lang in LOCALES:
        row = f"{lang:>6}  " + "  ".join(f"{stats[lang][d]:>16}" for d in DOMAINS)
        print(row)

    if missing_source:
        print("\n[WARN] Missing source files:\n" + "\n".join(f"  {p}" for p in missing_source))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print routing summary without writing any files.")
    args = parser.parse_args()

    if args.dry_run:
        print("=== DRY RUN — no files written ===")
    else:
        print("=== Migrating locale files ===")

    migrate(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
