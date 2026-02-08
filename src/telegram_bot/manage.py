import os
import sys
import argparse
from pathlib import Path

# Путь к шаблонам
TEMPLATES_DIR = Path(__file__).parent / "resources" / "templates" / "feature"

def load_template(name: str) -> str:
    """Загружает шаблон из файла."""
    path = TEMPLATES_DIR / f"{name}.tpl"
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {path}")
    return path.read_text(encoding="utf-8")

def create_feature(name: str):
    base_path = Path(__file__).parent / "features" / name
    
    if base_path.exists():
        print(f"❌ Ошибка: Фича '{name}' уже существует!")
        return

    # Преобразование имен: my_feature -> MyFeature
    class_name = "".join(word.capitalize() for word in name.split("_"))
    feature_key = name.lower()

    # Структура папок
    dirs = [
        base_path,
        base_path / "handlers",
        base_path / "logic",
        base_path / "ui",
        base_path / "resources",
        base_path / "contracts",
        base_path / "tests", # <-- Новая папка
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        # Создаем __init__.py везде
        (d / "__init__.py").write_text("", encoding="utf-8")

    # Загружаем шаблоны
    try:
        templates = {
            "feature.py": load_template("feature.py"),
            "handlers.py": load_template("handlers.py"),
            "orchestrator.py": load_template("orchestrator.py"),
            "state_manager.py": load_template("state_manager.py"),
            "ui.py": load_template("ui.py"),
            "contract.py": load_template("contract.py"),
            "test_orchestrator.py": load_template("test_orchestrator.py"), # <-- Новый шаблон
            # Ресурсы
            "callbacks.py": load_template("callbacks.py"),
            "texts.py": load_template("texts.py"),
            "formatters.py": load_template("formatters.py"),
            "keyboards.py": load_template("keyboards.py"),
        }
    except FileNotFoundError as e:
        print(f"❌ Ошибка: {e}")
        return

    # Создаем файлы с контентом
    files = {
        base_path / "feature_setting.py": templates["feature.py"],
        base_path / "handlers" / "handlers.py": templates["handlers.py"],
        base_path / "logic" / "orchestrator.py": templates["orchestrator.py"],
        base_path / "logic" / "state_manager.py": templates["state_manager.py"],
        base_path / "ui" / "ui.py": templates["ui.py"],
        base_path / "contracts" / "contract.py": templates["contract.py"],
        base_path / "tests" / "test_orchestrator.py": templates["test_orchestrator.py"], # <-- Создаем файл
        # Ресурсы
        base_path / "resources" / "callbacks.py": templates["callbacks.py"],
        base_path / "resources" / "texts.py": templates["texts.py"],
        base_path / "resources" / "formatters.py": templates["formatters.py"],
        base_path / "resources" / "keyboards.py": templates["keyboards.py"],
    }

    for path, template in files.items():
        content = template.format(class_name=class_name, feature_key=feature_key)
        path.write_text(content, encoding="utf-8")

    print(f"✅ Фича '{name}' успешно создана в {base_path}")
    print(f"👉 Не забудь добавить 'features.{name}' в INSTALLED_FEATURES (settings.py)")

def main():
    parser = argparse.ArgumentParser(description="Утилиты управления Telegram ботом")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Команда create_feature
    create_parser = subparsers.add_parser("create_feature", help="Создать новую фичу")
    create_parser.add_argument("name", help="Название фичи (snake_case, например: my_shop)")

    args = parser.parse_args()

    if args.command == "create_feature":
        create_feature(args.name)

if __name__ == "__main__":
    main()
