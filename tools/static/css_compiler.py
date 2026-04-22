#!/usr/bin/env python3
"""
CSS Compiler for LILY project.

Compiles CSS entry points by resolving all @import statements.
Reads mapping from compiler_config.json in the target static/css/ directory.

Config format (new, canonical):
    {
        "css": {
            "base.css": "app.css",
            "cabinet.css": "cabinet_app.css"
        }
    }

Usage:
    python tools/static/css_compiler.py --static-dir src/lily_backend/static
    python tools/static/css_compiler.py --static-dir src/backend_django/static
    python tools/static/css_compiler.py          # defaults to src/lily_backend/static
"""

import argparse
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_STATIC_DIR = PROJECT_ROOT / "src" / "lily_backend" / "static"


def read_css_file(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  ERROR reading {file_path}: {e}")
        return ""


def resolve_imports(css_content: str, base_path: Path) -> str:
    """Recursively resolve all @import url(...) statements."""
    import_pattern = r"@import\s+url\(['\"](.+?)['\"]\)(?:\s+(.+?))?;"

    def replace_import(match: re.Match) -> str:
        import_path = match.group(1)
        media_query = match.group(2)
        full_path = (base_path / import_path).resolve()

        if not full_path.exists():
            print(f"  WARNING: not found: {full_path}")
            return f"/* Import not found: {import_path} */"

        content = read_css_file(full_path)
        content = resolve_imports(content, full_path.parent)

        if media_query:
            return f"/* {import_path} */\n@media {media_query} {{\n{content}\n}}"
        return f"/* {import_path} */\n{content}"

    return re.sub(import_pattern, replace_import, css_content)


def remove_comments(css_content: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css_content, flags=re.DOTALL)


def compile_entry(source: Path, output: Path) -> None:
    print(f"  {source.name} -> {output.name}")
    content = read_css_file(source)
    if not content:
        return

    content = resolve_imports(content, source.parent)
    content = remove_comments(content)

    header = f"/*\n * Compiled CSS — DO NOT EDIT\n * Source: {source.name}\n */\n\n"
    output.write_text(header + content, encoding="utf-8")
    print(f"    -> {output.stat().st_size:,} bytes")


def load_css_config(css_dir: Path) -> dict[str, str]:
    """Load compiler_config.json and extract css section.

    Supports both formats:
      - New (canonical): {"css": {"base.css": "app.css"}, ...}
      - Old (flat):      {"base.css": "app.css"}
    """
    config_path = css_dir / "compiler_config.json"
    if not config_path.exists():
        print(f"  ERROR: config not found: {config_path}")
        return {}

    data = json.loads(config_path.read_text(encoding="utf-8"))

    if "css" in data and isinstance(data["css"], dict):
        return data["css"]

    # Old flat format — everything is a string→string mapping
    return {k: v for k, v in data.items() if isinstance(v, str)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile CSS @import chains into single files.")
    parser.add_argument(
        "--static-dir",
        default=str(DEFAULT_STATIC_DIR),
        metavar="PATH",
        help=f"Path to static directory (default: {DEFAULT_STATIC_DIR})",
    )
    args = parser.parse_args()

    static_dir = Path(args.static_dir)
    css_dir = static_dir / "css"

    if not css_dir.exists():
        print(f"ERROR: css dir not found: {css_dir}")
        return

    mapping = load_css_config(css_dir)
    if not mapping:
        print("No CSS entries found in config.")
        return

    print(f"Static: {static_dir}")
    print(f"Entries: {len(mapping)}")
    print()

    for source_file, output_file in mapping.items():
        source = css_dir / source_file
        output = css_dir / output_file
        if not source.exists():
            print(f"  SKIP {source_file}: not found")
            continue
        compile_entry(source, output)

    print("\nDone.")


if __name__ == "__main__":
    main()
