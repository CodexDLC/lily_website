"""
Add Module — восстановление модулей из git истории.

После установки первый коммит "Install" содержит ВСЕ файлы шаблона.
Эта команда достаёт нужный модуль обратно:

  python -m tools.init_project.add_module bot
  python -m tools.init_project.add_module fastapi
  python -m tools.init_project.add_module shared

Работает через: git checkout <install-hash> -- <paths>
Без интернета, всё из локальной git истории.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Маппинг модулей на пути в шаблоне
MODULE_PATHS: dict[str, list[str]] = {
    "bot": [
        "src/telegram_bot",
    ],
    "fastapi": [
        "src/backend-fastapi",
    ],
    "django": [
        "src/backend-django",
    ],
    "shared": [
        "src/shared",
    ],
}


def _get_install_hash() -> str | None:
    """Читает hash коммита 'Install' из файла."""
    hash_file = PROJECT_ROOT / ".template_install_hash"
    if hash_file.exists():
        return hash_file.read_text(encoding="utf-8").strip()

    # Fallback: ищем по сообщению коммита
    try:
        result = subprocess.run(
            ["git", "log", "--all", "--oneline", "--grep=Install: template snapshot"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split()[0]
    except FileNotFoundError:
        pass

    return None


def _restore_module(module_name: str) -> None:
    """Восстанавливает модуль из коммита Install."""
    if module_name not in MODULE_PATHS:
        print(f"❌ Unknown module: {module_name}")
        print(f"   Available: {', '.join(MODULE_PATHS.keys())}")
        sys.exit(1)

    install_hash = _get_install_hash()
    if not install_hash:
        print("❌ Install commit not found.")
        print("   This project may not have been created from the template.")
        sys.exit(1)

    paths = MODULE_PATHS[module_name]

    for rel_path in paths:
        full_path = PROJECT_ROOT / rel_path
        if full_path.exists():
            print(f"⚠️  {rel_path} already exists — skipping")
            continue

        try:
            subprocess.run(
                ["git", "checkout", install_hash, "--", rel_path],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
            )
            print(f"✅ Restored: {rel_path}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to restore: {rel_path}")
            print(f"   (not found in Install commit {install_hash[:8]})")

    print()
    print(f"📦 Module '{module_name}' restored from template.")
    print("   Don't forget to update pyproject.toml dependencies and Docker config!")


def main() -> None:
    print()
    print("═" * 45)
    print("  📦 Add Module from Template")
    print("═" * 45)
    print()

    if len(sys.argv) < 2:
        print("Usage: python -m tools.init_project.add_module <module>")
        print()
        print("Available modules:")
        for name, paths in MODULE_PATHS.items():
            print(f"  {name:10s} → {', '.join(paths)}")
        sys.exit(0)

    module_name = sys.argv[1].lower()
    _restore_module(module_name)


if __name__ == "__main__":
    main()
