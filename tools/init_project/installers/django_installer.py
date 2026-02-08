"""
Django Installer — создание структуры Django проекта.

Flow:
  pre_install  — ничего (зависимости через PoetryAction)
  install      — создаёт полную Django структуру из шаблонов:
                 core/ (settings split), features/ (main + system),
                 static/, templates/, locale/
  post_install — проверка что manage.py существует

Не использует django-admin startproject / startapp напрямую,
потому что наша структура сильно отличается от стандартной Django:
  - core/ вместо project_name/
  - settings/ папка (base/dev/prod) вместо settings.py
  - features/ вместо apps в корне
  - views/ и models/ как папки, не файлы
  - selectors/ слой для чтения данных
"""

from __future__ import annotations

from pathlib import Path

from tools.init_project.config import InstallContext  # noqa: TC001
from tools.init_project.installers.base import BaseInstaller

# Путь к ресурсам Django
RESOURCES_DIR = Path(__file__).parent / "django" / "resources"


class DjangoInstaller(BaseInstaller):
    name = "Django"

    def pre_install(self, ctx: InstallContext) -> None:
        print("    🐍 Django installer — preparing...")

    def install(self, ctx: InstallContext) -> None:
        """Создаёт полную Django структуру из шаблонов."""
        backend_dir = ctx.project_root / "src" / "backend_django"

        # ── 1. Core (settings, urls, wsgi, asgi) ──
        self._create_core(backend_dir, ctx.project_name)

        # ── 2. Features: main + system ──
        self._create_feature_main(backend_dir, ctx.project_name)
        self._create_feature_system(backend_dir, ctx.project_name)

        # ── 3. Static / Templates / Locale ──
        self._create_static_dirs(backend_dir)
        self._create_templates(backend_dir, ctx.project_name)
        self._create_locale(backend_dir)

        # ── 4. Root files (manage.py, .env, README) ──
        self._create_root_files(backend_dir, ctx.project_name)

        print("    ✅ Django structure created")

    def post_install(self, ctx: InstallContext) -> None:
        manage = ctx.project_root / "src" / "backend_django" / "manage.py"
        if manage.exists():
            print("    ✅ manage.py verified")
        else:
            print("    ⚠️  manage.py not found — something went wrong")

    # ─────────────────────────────────────────
    # Core
    # ─────────────────────────────────────────

    def _create_core(self, backend_dir: Path, project_name: str) -> None:
        """Создаёт core/ с split settings."""
        core_dir = backend_dir / "core"
        settings_dir = core_dir / "settings"
        settings_dir.mkdir(parents=True, exist_ok=True)

        # Core files
        tpl_core = RESOURCES_DIR / "core"
        self._render(tpl_core / "__init__.py.tpl", core_dir / "__init__.py", project_name)
        self._render(tpl_core / "urls.py.tpl", core_dir / "urls.py", project_name)
        self._render(tpl_core / "asgi.py.tpl", core_dir / "asgi.py", project_name)
        self._render(tpl_core / "wsgi.py.tpl", core_dir / "wsgi.py", project_name)

        # Settings
        tpl_settings = tpl_core / "settings"
        self._render(tpl_settings / "__init__.py.tpl", settings_dir / "__init__.py", project_name)
        self._render(tpl_settings / "base.py.tpl", settings_dir / "base.py", project_name)
        self._render(tpl_settings / "dev.py.tpl", settings_dir / "dev.py", project_name)
        self._render(tpl_settings / "prod.py.tpl", settings_dir / "prod.py", project_name)

        print("    ✅ core/ (settings split: base/dev/prod)")

    # ─────────────────────────────────────────
    # Features
    # ─────────────────────────────────────────

    def _create_feature_main(self, backend_dir: Path, project_name: str) -> None:
        """Создаёт features/main/ — стартовая feature с views/ и selectors/."""
        feat_dir = backend_dir / "features" / "main"
        views_dir = feat_dir / "views"
        selectors_dir = feat_dir / "selectors"
        migrations_dir = feat_dir / "migrations"

        for d in [views_dir, selectors_dir, migrations_dir]:
            d.mkdir(parents=True, exist_ok=True)

        tpl = RESOURCES_DIR / "feature_tpl"

        # __init__.py
        self._render(tpl / "__init__.py.tpl", feat_dir / "__init__.py", project_name)

        # apps.py
        self._render_feature_apps(
            tpl / "apps.py.tpl",
            feat_dir / "apps.py",
            app_name="main",
            app_class="Main",
            app_verbose="Main",
        )

        # admin.py, tests.py
        self._render(tpl / "admin.py.tpl", feat_dir / "admin.py", project_name)
        self._render(tpl / "tests.py.tpl", feat_dir / "tests.py", project_name)

        # urls.py
        self._render(tpl / "urls.py.tpl", feat_dir / "urls.py", project_name, extra={"{{APP_NAME}}": "main"})

        # models.py (пустой, можно потом сделать папку)
        (feat_dir / "models.py").write_text("# from django.db import models\n", encoding="utf-8")

        # views/__init__.py + views/home.py
        (views_dir / "__init__.py").write_text("", encoding="utf-8")
        self._render(tpl / "home_view.py.tpl", views_dir / "home.py", project_name)

        # selectors/__init__.py
        (selectors_dir / "__init__.py").write_text("", encoding="utf-8")

        # migrations/__init__.py
        (migrations_dir / "__init__.py").write_text("", encoding="utf-8")

        print("    ✅ features/main/ (views/, selectors/, urls)")

    def _create_feature_system(self, backend_dir: Path, project_name: str) -> None:
        """Создаёт features/system/ — сервисные модели (mixins, tags и т.д.)."""
        feat_dir = backend_dir / "features" / "system"
        models_dir = feat_dir / "models"
        migrations_dir = feat_dir / "migrations"

        for d in [models_dir, migrations_dir]:
            d.mkdir(parents=True, exist_ok=True)

        tpl = RESOURCES_DIR / "feature_tpl"

        # __init__.py
        self._render(tpl / "__init__.py.tpl", feat_dir / "__init__.py", project_name)

        # apps.py
        self._render_feature_apps(
            tpl / "apps.py.tpl",
            feat_dir / "apps.py",
            app_name="system",
            app_class="System",
            app_verbose="System",
        )

        # admin.py, tests.py
        self._render(tpl / "admin.py.tpl", feat_dir / "admin.py", project_name)
        self._render(tpl / "tests.py.tpl", feat_dir / "tests.py", project_name)

        # models/__init__.py + models/mixins.py
        (models_dir / "__init__.py").write_text(
            "from .mixins import TimestampMixin  # noqa: F401\n",
            encoding="utf-8",
        )
        self._render(tpl / "mixins.py.tpl", models_dir / "mixins.py", project_name)

        # migrations/__init__.py
        (migrations_dir / "__init__.py").write_text("", encoding="utf-8")

        # features/__init__.py
        features_init = backend_dir / "features" / "__init__.py"
        if not features_init.exists():
            features_init.write_text("", encoding="utf-8")

        print("    ✅ features/system/ (models/mixins, service layer)")

    # ─────────────────────────────────────────
    # Static / Templates / Locale
    # ─────────────────────────────────────────

    def _create_static_dirs(self, backend_dir: Path) -> None:
        """Создаёт static/css, static/js, static/img."""
        for sub in ["css", "js", "img"]:
            d = backend_dir / "static" / sub
            d.mkdir(parents=True, exist_ok=True)

        # Минимальный base.css
        css_file = backend_dir / "static" / "css" / "base.css"
        if not css_file.exists():
            css_file.write_text(
                "/* Base styles for the project */\n"
                "*, *::before, *::after { box-sizing: border-box; }\n"
                "body { margin: 0; font-family: system-ui, sans-serif; }\n",
                encoding="utf-8",
            )

        print("    ✅ static/ (css/, js/, img/)")

    def _create_templates(self, backend_dir: Path, project_name: str) -> None:
        """Создаёт templates/base.html и templates/home/home.html."""
        templates_dir = backend_dir / "templates"
        home_dir = templates_dir / "home"
        home_dir.mkdir(parents=True, exist_ok=True)

        self._render(RESOURCES_DIR / "base.html.tpl", templates_dir / "base.html", project_name)
        self._render(RESOURCES_DIR / "home.html.tpl", home_dir / "home.html", project_name)

        print("    ✅ templates/ (base.html, home/home.html)")

    def _create_locale(self, backend_dir: Path) -> None:
        """Создаёт пустую locale/ структуру для i18n."""
        locale_dir = backend_dir / "locale"
        locale_dir.mkdir(parents=True, exist_ok=True)
        print("    ✅ locale/ (ready for i18n)")

    # ─────────────────────────────────────────
    # Root files
    # ─────────────────────────────────────────

    def _create_root_files(self, backend_dir: Path, project_name: str) -> None:
        """Создаёт manage.py, .env, .env.example, __init__.py, README.md."""
        # __init__.py
        init_file = backend_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text("", encoding="utf-8")

        # manage.py
        self._render(RESOURCES_DIR / "manage.py.tpl", backend_dir / "manage.py", project_name)

        # .env + .env.example
        self._render(RESOURCES_DIR / "env.tpl", backend_dir / ".env", project_name)
        self._render(RESOURCES_DIR / "env.example.tpl", backend_dir / ".env.example", project_name)

        # README.md
        self._render(RESOURCES_DIR / "README.md.tpl", backend_dir / "README.md", project_name)

        print("    ✅ manage.py, .env, .env.example, README.md")

    # ─────────────────────────────────────────
    # Template rendering helpers
    # ─────────────────────────────────────────

    @staticmethod
    def _render(
        tpl_path: Path,
        output_path: Path,
        project_name: str,
        *,
        extra: dict[str, str] | None = None,
    ) -> None:
        """Читает .tpl, заменяет маркеры, пишет результат."""
        if not tpl_path.exists():
            return

        content = tpl_path.read_text(encoding="utf-8")
        content = content.replace("{{PROJECT_NAME}}", project_name)

        if extra:
            for marker, value in extra.items():
                content = content.replace(marker, value)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

    @staticmethod
    def _render_feature_apps(
        tpl_path: Path,
        output_path: Path,
        *,
        app_name: str,
        app_class: str,
        app_verbose: str,
    ) -> None:
        """Рендерит apps.py для feature с заменой APP маркеров."""
        if not tpl_path.exists():
            return

        content = tpl_path.read_text(encoding="utf-8")
        content = content.replace("{{APP_NAME}}", app_name)
        content = content.replace("{{APP_CLASS}}", app_class)
        content = content.replace("{{APP_VERBOSE}}", app_verbose)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
