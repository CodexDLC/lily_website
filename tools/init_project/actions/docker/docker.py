"""
Docker Action — генерация Docker файлов на основе выбора пользователя.

Читает .tpl шаблоны из resources/, подставляет переменные,
записывает готовые файлы в deploy/ и корень проекта.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from tools.init_project.config import InstallContext, safe_rmtree

# Путь к ресурсам относительно этого файла
RESOURCES = Path(__file__).parent / "resources"

PYTHON_VERSION = "3.13"


class DockerAction:
    """Генерация Docker-инфраструктуры из шаблонов."""

    def execute(self, ctx: InstallContext) -> None:
        deploy = ctx.project_root / "deploy"

        # Очищаем старый deploy (из шаблона-донора)
        if deploy.exists():
            safe_rmtree(deploy)
        deploy.mkdir(parents=True)

        # Переменные для подстановки
        variables = {
            "{{PROJECT_NAME}}": ctx.project_name,
            "{{PYTHON_VERSION}}": PYTHON_VERSION,
            "{{DOMAIN}}": f"{ctx.project_name}.dev",  # default, user поменяет
        }

        # ── Dockerfiles ──
        if ctx.backend == "fastapi":
            self._render_template(
                RESOURCES / "fastapi" / "Dockerfile.tpl",
                deploy / "fastapi" / "Dockerfile",
                variables,
            )
            print("    📄 Generated: deploy/fastapi/Dockerfile")

        if ctx.include_bot:
            self._render_template(
                RESOURCES / "02_telegram_bot" / "Dockerfile.tpl",
                deploy / "02_telegram_bot" / "Dockerfile",
                variables,
            )
            print("    📄 Generated: deploy/02_telegram_bot/Dockerfile")

            self._render_template(
                RESOURCES / "worker_arq" / "Dockerfile.tpl",
                deploy / "worker_arq" / "Dockerfile",
                variables,
            )
            print("    📄 Generated: deploy/worker_arq/Dockerfile")

        # ── Nginx (только если есть бэкенд) ──
        if ctx.backend:
            nginx_dir = deploy / "nginx"
            nginx_dir.mkdir(parents=True, exist_ok=True)

            self._render_template(
                RESOURCES / "nginx" / "Dockerfile.tpl",
                nginx_dir / "Dockerfile",
                variables,
            )
            self._render_template(
                RESOURCES / "nginx" / "nginx-main.conf.tpl",
                nginx_dir / "nginx-main.conf",
                variables,
            )
            self._render_template(
                RESOURCES / "nginx" / "site.conf.tpl",
                nginx_dir / "site.conf",
                variables,
            )
            self._render_template(
                RESOURCES / "nginx" / "site-local.conf.tpl",
                nginx_dir / "site-local.conf",
                variables,
            )
            print("    📄 Generated: deploy/nginx/ (4 files)")

        # ── docker-compose ──
        self._generate_compose_dev(ctx, deploy, variables)
        self._generate_compose_prod(ctx, deploy, variables)

        # ── .dockerignore ──
        self._render_template(
            RESOURCES / "dockerignore.tpl",
            ctx.project_root / ".dockerignore",
            variables,
        )
        print("    📄 Generated: .dockerignore")

        # ── CI/CD Workflows ──
        self._generate_workflows(ctx, variables)

    # ─────────────────────────────────────────
    # CI/CD generation
    # ─────────────────────────────────────────

    def _generate_workflows(self, ctx: InstallContext, variables: dict[str, str]) -> None:
        """Генерирует GitHub Actions workflows."""
        workflows_dir = ctx.project_root / ".github" / "workflows"

        # Удаляем старые workflows
        if workflows_dir.exists():
            safe_rmtree(workflows_dir)
        workflows_dir.mkdir(parents=True, exist_ok=True)

        # Общие переменные для CI
        extras: list[str] = []
        lint_paths: list[str] = []
        if ctx.backend == "fastapi":
            extras.append("fastapi")
            lint_paths.append("src/backend-fastapi/")
        if ctx.include_bot:
            extras.append("02_telegram_bot")
            lint_paths.append("src/telegram_bot/")
        lint_paths.append("src/shared/")

        install_extras = "," + ",".join(extras) if extras else ""

        ci_vars = {
            **variables,
            "{{INSTALL_EXTRAS}}": install_extras,
            "{{LINT_PATHS}}": " ".join(lint_paths),
        }

        # ci-develop.yml
        self._render_template(
            RESOURCES / "github" / "ci-develop.yml.tpl",
            workflows_dir / "ci-develop.yml",
            ci_vars,
        )

        # ci-main.yml — нужны динамические блоки
        services_block = ""
        test_env = '          SECRET_KEY: "test_secret_key_for_ci"'
        build_steps = ""

        if ctx.backend == "fastapi":
            services_block = dedent("""\
                services:
                  db:
                    image: postgres:16
                    env:
                      POSTGRES_DB: test_db
                      POSTGRES_PASSWORD: test_password
                    ports: ["5432:5432"]
                    options: >-
                      --health-cmd pg_isready
                      --health-interval 10s
                      --health-timeout 5s
                      --health-retries 5""")
            test_env += "\n          DATABASE_URL: postgresql+asyncpg://postgres:test_password@localhost:5432/test_db"
            build_steps += dedent("""\
                  - name: Build FastAPI image
                    run: docker build -f deploy/fastapi/Dockerfile -t check-backend .""")

        if ctx.include_bot:
            build_steps += dedent("""\
                  - name: Build Bot image
                    run: docker build -f deploy/02_telegram_bot/Dockerfile -t check-02_telegram_bot .""")

        main_vars = {
            **ci_vars,
            "{{SERVICES_BLOCK}}": ("    " + services_block) if services_block else "",
            "{{TEST_ENV_VARS}}": test_env,
            "{{BUILD_STEPS}}": build_steps,
        }
        self._render_template(
            RESOURCES / "github" / "ci-main.yml.tpl",
            workflows_dir / "ci-main.yml",
            main_vars,
        )

        # cd-release.yml — build+push для каждого образа
        build_push = ""
        export_images = ""
        migrate_step = ""

        if ctx.backend == "fastapi":
            build_push += dedent("""\
                  - name: Build and Push Backend
                    uses: docker/build-push-action@v5
                    with:
                      context: .
                      file: deploy/fastapi/Dockerfile
                      push: true
                      tags: ghcr.io/${{ env.REPO_LOWER }}:latest

                  - name: Build and Push Nginx
                    uses: docker/build-push-action@v5
                    with:
                      context: .
                      file: deploy/nginx/Dockerfile
                      push: true
                      tags: ghcr.io/${{ env.REPO_LOWER }}-nginx:latest""")
            export_images += dedent("""\
                        export DOCKER_IMAGE_BACKEND=ghcr.io/$REPO_LOWER:latest
                        export DOCKER_IMAGE_NGINX=ghcr.io/$REPO_LOWER-nginx:latest""")
            # Run Alembic migrations BEFORE starting services (avoids race condition)
            migrate_step = (
                "            docker compose -f deploy/docker-compose.prod.yml run --rm -T backend alembic upgrade head"
            )

        if ctx.backend == "django":
            # Django: collectstatic + migrate before starting
            migrate_step = dedent("""\
                        docker compose -f deploy/docker-compose.prod.yml run --rm -T backend python manage.py migrate --noinput
                        docker compose -f deploy/docker-compose.prod.yml run --rm -T backend python manage.py collectstatic --noinput""")

        if ctx.include_bot:
            build_push += dedent("""\

                  - name: Build and Push Bot
                    uses: docker/build-push-action@v5
                    with:
                      context: .
                      file: deploy/02_telegram_bot/Dockerfile
                      push: true
                      tags: ghcr.io/${{ env.REPO_LOWER }}-02_telegram_bot:latest

                  - name: Build and Push Worker
                    uses: docker/build-push-action@v5
                    with:
                      context: .
                      file: deploy/worker_arq/Dockerfile
                      push: true
                      tags: ghcr.io/${{ env.REPO_LOWER }}-worker_arq:latest""")
            export_images += dedent("""\

                        export DOCKER_IMAGE_BOT=ghcr.io/$REPO_LOWER-02_telegram_bot:latest
                        export DOCKER_IMAGE_WORKER=ghcr.io/$REPO_LOWER-worker_arq:latest""")

        release_vars = {
            **variables,
            "{{BUILD_PUSH_STEPS}}": build_push,
            "{{EXPORT_IMAGES}}": export_images,
            "{{MIGRATE_STEP}}": migrate_step,
        }
        self._render_template(
            RESOURCES / "github" / "cd-release.yml.tpl",
            workflows_dir / "cd-release.yml",
            release_vars,
        )

        # check-release-source.yml — копируем как есть
        self._render_template(
            RESOURCES / "github" / "check-release-source.yml",
            workflows_dir / "check-release-source.yml",
            {},
        )

        print("    📄 Generated: .github/workflows/ (4 files)")

    # ─────────────────────────────────────────
    # Compose generation — секционная сборка
    # ─────────────────────────────────────────

    def _generate_compose_dev(self, ctx: InstallContext, deploy: Path, variables: dict[str, str]) -> None:
        """Генерирует docker-compose.yml для dev."""
        services: list[str] = []
        volumes: list[str] = []
        net = ctx.project_name

        if ctx.backend == "fastapi":
            services.append(self._svc_backend_dev(ctx.project_name))
            volumes.extend(["uploads:\n    driver: local", "logs:\n    driver: local"])

        if ctx.include_bot:
            services.append(self._svc_bot_dev(ctx.project_name))
            services.append(self._svc_worker_dev(ctx.project_name))

        # Redis — если бот (FSM storage + ARQ)
        if ctx.include_bot:
            services.append(self._svc_redis(ctx.project_name))
            volumes.append("redis-data:\n    driver: local")

        # Postgres — если FastAPI
        if ctx.backend == "fastapi":
            services.append(self._svc_postgres(ctx.project_name))
            volumes.append("postgres-data:\n    driver: local")

        # Nginx — если бэкенд
        if ctx.backend:
            services.append(self._svc_nginx_dev(ctx.project_name))

        compose = self._assemble_compose(services, volumes, net)
        (deploy / "docker-compose.yml").write_text(compose, encoding="utf-8")
        print("    📄 Generated: deploy/docker-compose.yml")

    def _generate_compose_prod(self, ctx: InstallContext, deploy: Path, variables: dict[str, str]) -> None:
        """Генерирует docker-compose.prod.yml."""
        services: list[str] = []
        volumes: list[str] = []
        net = ctx.project_name

        if ctx.backend == "fastapi":
            services.append(self._svc_backend_prod(ctx.project_name))
            volumes.extend(["uploads:\n    driver: local", "logs:\n    driver: local"])

        if ctx.include_bot:
            services.append(self._svc_bot_prod(ctx.project_name))
            services.append(self._svc_worker_prod(ctx.project_name))

        if ctx.include_bot:
            services.append(self._svc_redis(ctx.project_name))
            volumes.append("redis-data:\n    driver: local")

        if ctx.backend:
            services.append(self._svc_nginx_prod(ctx.project_name))

        compose = self._assemble_compose(services, volumes, net)
        (deploy / "docker-compose.prod.yml").write_text(compose, encoding="utf-8")
        print("    📄 Generated: deploy/docker-compose.prod.yml")

    @staticmethod
    def _assemble_compose(services: list[str], volumes: list[str], network_name: str) -> str:
        """Собирает docker-compose из блоков."""
        compose = "services:\n"
        compose += "\n\n".join(services)
        compose += "\n\nvolumes:\n"
        if volumes:
            compose += "\n".join(f"  {v}" for v in volumes)
        else:
            compose += "  {}"
        compose += f"\n\nnetworks:\n  {network_name}-network:\n    driver: bridge\n"
        return compose

    # ─────────────────────────────────────────
    # Service blocks — dev
    # ─────────────────────────────────────────

    @staticmethod
    def _svc_backend_dev(name: str) -> str:
        return dedent(f"""\
          backend:
            build:
              context: ..
              dockerfile: deploy/fastapi/Dockerfile
            container_name: {name}-backend
            env_file: ../.env
            volumes:
              - ../src/backend-fastapi:/app/src/backend-fastapi:ro
              - ../src/shared:/app/src/shared:ro
              - uploads:/app/data/uploads
              - logs:/app/data/logs
            expose:
              - "8000"
            healthcheck:
              test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
              interval: 30s
              timeout: 10s
              retries: 3
              start_period: 40s
            restart: unless-stopped
            depends_on:
              postgres:
                condition: service_healthy
            networks:
              - {name}-network""")

    @staticmethod
    def _svc_bot_dev(name: str) -> str:
        return dedent(f"""\
          02_telegram_bot:
            build:
              context: ..
              dockerfile: deploy/02_telegram_bot/Dockerfile
            container_name: {name}-02_telegram_bot
            env_file: ../.env
            volumes:
              - ../src/telegram_bot:/app/src/telegram_bot:ro
              - ../src/shared:/app/src/shared:ro
            restart: unless-stopped
            depends_on:
              - redis
            networks:
              - {name}-network""")

    @staticmethod
    def _svc_worker_dev(name: str) -> str:
        return dedent(f"""\
          worker_arq:
            build:
              context: ..
              dockerfile: deploy/worker_arq/Dockerfile
            container_name: {name}-worker_arq
            env_file: ../.env
            volumes:
              - ../src/telegram_bot:/app/src/telegram_bot:ro
              - ../src/shared:/app/src/shared:ro
            restart: unless-stopped
            depends_on:
              - redis
            networks:
              - {name}-network""")

    @staticmethod
    def _svc_redis(name: str) -> str:
        return dedent(f"""\
          redis:
            image: redis:7-alpine
            container_name: {name}-redis
            command: redis-server --appendonly yes
            volumes:
              - redis-data:/data
            expose:
              - "6379"
            healthcheck:
              test: ["CMD", "redis-cli", "ping"]
              interval: 10s
              timeout: 5s
              retries: 3
            restart: unless-stopped
            networks:
              - {name}-network""")

    @staticmethod
    def _svc_postgres(name: str) -> str:
        return dedent(f"""\
          postgres:
            image: postgres:16-alpine
            container_name: {name}-postgres
            environment:
              POSTGRES_DB: ${{POSTGRES_DB:-{name}}}
              POSTGRES_USER: ${{POSTGRES_USER:-postgres}}
              POSTGRES_PASSWORD: ${{POSTGRES_PASSWORD:-postgres}}
            volumes:
              - postgres-data:/var/lib/postgresql/data
            expose:
              - "5432"
            healthcheck:
              test: ["CMD-SHELL", "pg_isready -U postgres"]
              interval: 10s
              timeout: 5s
              retries: 5
            restart: unless-stopped
            networks:
              - {name}-network""")

    @staticmethod
    def _svc_nginx_dev(name: str) -> str:
        return dedent(f"""\
          nginx:
            image: nginx:alpine
            container_name: {name}-nginx
            ports:
              - "80:80"
            volumes:
              - ./nginx/nginx-main.conf:/etc/nginx/nginx.conf:ro
              - ./nginx/site-local.conf:/etc/nginx/conf.d/site.conf:ro
              - uploads:/app/media:ro
            depends_on:
              backend:
                condition: service_healthy
            restart: unless-stopped
            networks:
              - {name}-network""")

    # ─────────────────────────────────────────
    # Service blocks — prod
    # ─────────────────────────────────────────

    @staticmethod
    def _svc_backend_prod(name: str) -> str:
        return dedent(f"""\
          backend:
            image: ${{DOCKER_IMAGE_BACKEND}}
            container_name: {name}-backend
            env_file: .env
            volumes:
              - uploads:/app/data/uploads
              - logs:/app/data/logs
            expose:
              - "8000"
            restart: always
            networks:
              - {name}-network""")

    @staticmethod
    def _svc_bot_prod(name: str) -> str:
        return dedent(f"""\
          02_telegram_bot:
            image: ${{DOCKER_IMAGE_BOT}}
            container_name: {name}-02_telegram_bot
            env_file: .env
            restart: always
            depends_on:
              - redis
            networks:
              - {name}-network""")

    @staticmethod
    def _svc_worker_prod(name: str) -> str:
        return dedent(f"""\
          worker_arq:
            image: ${{DOCKER_IMAGE_WORKER}}
            container_name: {name}-worker_arq
            env_file: .env
            restart: always
            depends_on:
              - redis
            networks:
              - {name}-network""")

    @staticmethod
    def _svc_nginx_prod(name: str) -> str:
        return dedent(f"""\
          nginx:
            image: ${{DOCKER_IMAGE_NGINX}}
            container_name: {name}-nginx
            ports:
              - "80:80"
              - "443:443"
            volumes:
              - ./nginx/nginx-main.conf:/etc/nginx/nginx.conf:ro
              - ./nginx/site.conf:/etc/nginx/conf.d/site.conf:ro
              - uploads:/app/media:ro
            depends_on:
              - backend
            restart: always
            networks:
              - {name}-network
            logging:
              driver: "json-file"
              options:
                max-size: "10m"
                max-file: "3" """)

    # ─────────────────────────────────────────
    # Template rendering
    # ─────────────────────────────────────────

    @staticmethod
    def _render_template(template_path: Path, output_path: Path, variables: dict[str, str]) -> None:
        """Читает .tpl, подставляет переменные, записывает результат."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        content = template_path.read_text(encoding="utf-8")
        for marker, value in variables.items():
            content = content.replace(marker, value)
        output_path.write_text(content, encoding="utf-8")
