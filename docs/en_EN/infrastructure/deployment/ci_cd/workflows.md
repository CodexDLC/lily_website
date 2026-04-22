# 🚀 Workflows

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

The project uses GitHub Actions to automate testing, linting, and deployment.

## Pipelines

### 1. CI Main (`ci-main.yml`)
- **Trigger:** Pull Request to `main`.
- **Jobs:**
  - **Tests:** Runs `pytest` with a service container (`postgres:15`).
  - **Build Check:** Verifies that the Docker image builds successfully.
  - **Security:** Scans built images with Trivy.
  - **Integration:** Runs full stack integration tests via `docker compose`.

### 2. CI Develop (`ci-develop.yml`)
- **Trigger:** Push to `develop`.
- **Jobs:**
  - **Lint:** Runs `ruff` (style) and `mypy` (types) to ensure code quality during development.
  - **Security:** Scans file system for vulnerabilities and secrets with Trivy.

### 3. CD Production (`deploy-production-tag.yml`)
- **Trigger:** Push tag `v*` (e.g., `v1.2.3`).
- **Jobs:**
  - **Deploy:**
    1. Builds Backend, Bot, Worker, and Nginx Docker images.
    2. Pushes images to GitHub Container Registry (GHCR).
    3. Copies `docker-compose.prod.yml` to the VPS via SCP.
    4. Connects via SSH to:
       - Update `.env` file.
       - Pull new images.
       - Restart containers (`docker compose up -d`).
       - Run database migrations (`python manage.py migrate`).
       - Collect static files (`python manage.py collectstatic`).
       - Prune old images.

### 4. Archived Workflows
- `cd-release.yml` (Removed)
- `check-release-source.yml` (Removed)
