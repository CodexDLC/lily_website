#!/usr/bin/env python3
"""
Скрипт для добавления fallback в font-family с CSS переменными.

Заменяет:
    font-family: var(--font-serif);
    font-family: var(--font-sans);
На:
    font-family: var(--font-serif, serif);
    font-family: var(--font-sans, sans-serif);

Использование:
    python tools/fix_font_fallback.py
"""

import re
from pathlib import Path


def fix_font_fallback(content: str) -> tuple[str, int]:
    """
    Добавляет fallback к font-family с переменными.

    Returns:
        tuple: (исправленный контент, количество замен)
    """
    replacements = 0

    # Замена для serif
    new_content, count = re.subn(
        r"font-family:\s*var\(--font-serif\);", "font-family: var(--font-serif, serif);", content
    )
    replacements += count

    # Замена для sans
    new_content, count = re.subn(
        r"font-family:\s*var\(--font-sans\);", "font-family: var(--font-sans, sans-serif);", new_content
    )
    replacements += count

    return new_content, replacements


def process_file(file_path: Path) -> int:
    """
    Обрабатывает один CSS файл.

    Returns:
        int: Количество замен
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        new_content, replacements = fix_font_fallback(content)

        if replacements > 0:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"✅ {file_path.name}: {replacements} замен(ы)")

        return replacements

    except Exception as e:
        print(f"❌ Ошибка обработки {file_path}: {e}")
        return 0


def main():
    """Главная функция."""
    print("🔧 Исправление font-family fallback...")

    # Определяем пути
    project_root = Path(__file__).parent.parent
    css_dir = project_root / "src" / "backend_django" / "static" / "css"

    if not css_dir.exists():
        print(f"❌ Директория не найдена: {css_dir}")
        return

    # Находим все CSS файлы (кроме app.css - он генерируется)
    css_files = [f for f in css_dir.rglob("*.css") if f.name != "app.css" and "_old" not in str(f)]

    if not css_files:
        print("❌ CSS файлы не найдены")
        return

    print(f"📁 Найдено {len(css_files)} файлов\n")

    # Обрабатываем файлы
    total_replacements = 0
    for css_file in sorted(css_files):
        replacements = process_file(css_file)
        total_replacements += replacements

    print(f"\n✅ Готово! Всего замен: {total_replacements}")
    print("\n💡 Не забудь скомпилировать CSS:")
    print("   python tools/css_compiler.py")


if __name__ == "__main__":
    main()
