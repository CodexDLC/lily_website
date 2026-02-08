# 🔄 GitHub Actions Workflows

This directory is populated by the installer (`python -m tools.init_project`).

Based on your module selection, the following workflows will be generated:

| Workflow | Trigger | Purpose |
|:---------|:--------|:--------|
| `ci-develop.yml` | Push to develop | Lint (ruff, mypy) |
| `ci-main.yml` | PR to main | Tests + Docker build |
| `cd-release.yml` | Push to release | Build → GHCR → Deploy via SSH |
| `check-release-source.yml` | PR to release | Verify source is main branch |

Templates are stored in: `tools/init_project/actions/docker/resources/github/`

See also: `docs/en_EN/infrastructure/devops/` for setup instructions.
