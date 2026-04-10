"""
tools/dump_by_model.py — Split a Django JSON fixture into per-model files.

Usage:
    python tools/dump_by_model.py --input data/prod.json --output data/prod_dump/
    python tools/dump_by_model.py --input data/prod.json  # uses default output dir

Output:
    data/prod_dump/booking.client.json
    data/prod_dump/booking.appointment.json
    data/prod_dump/system.sitesettings.json
    ...

Each output file is a valid Django JSON fixture loadable via:
    python manage.py loaddata data/prod_dump/booking.client.json
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "prod_dump"


def split_dump(input_path: Path, output_dir: Path) -> dict[str, int]:
    """Parse dump and write one file per model. Returns {model_label: record_count}."""
    raw = input_path.read_text(encoding="utf-8")
    try:
        records = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: Could not parse JSON — {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(records, list):
        print("ERROR: Expected a JSON array at top level.", file=sys.stderr)
        sys.exit(1)

    by_model: defaultdict[str, list] = defaultdict(list)
    skipped = 0
    for record in records:
        model = record.get("model")
        if not model:
            skipped += 1
            continue
        by_model[model].append(record)

    if skipped:
        print(f"WARNING: {skipped} records had no 'model' field and were skipped.")

    output_dir.mkdir(parents=True, exist_ok=True)

    counts: dict[str, int] = {}
    for model_label, model_records in sorted(by_model.items()):
        filename = f"{model_label}.json"
        out_path = output_dir / filename
        out_path.write_text(
            json.dumps(model_records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        counts[model_label] = len(model_records)

    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Split a Django JSON fixture dump into one file per model.")
    parser.add_argument(
        "--input",
        required=True,
        metavar="FILE",
        help="Path to the full Django JSON dump file.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        metavar="DIR",
        help=f"Output directory (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output)

    print(f"Input:  {input_path}")
    print(f"Output: {output_dir}")
    print()

    counts = split_dump(input_path, output_dir)

    if not counts:
        print("No records found in dump.")
        return

    max_label_len = max(len(label) for label in counts)
    total = 0
    for label, count in sorted(counts.items()):
        print(f"  {label:<{max_label_len}}  {count:>6} records  →  {label}.json")
        total += count

    print()
    print(f"Done. {len(counts)} model files written, {total} total records.")
    print(f"Output directory: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
