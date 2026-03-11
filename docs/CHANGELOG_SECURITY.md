# Security Changelog

## [Unreleased]

### Added
- **CI/CD Security Scanning:**
  - Added `Trivy` filesystem scan to `ci-develop.yml` to detect vulnerabilities and secrets in the codebase.
  - Added `Trivy` image scan to `ci-main.yml` to scan built Docker images for OS and library vulnerabilities.
  - Added `pip-audit` to `pyproject.toml` for checking known vulnerabilities in Python dependencies.

### Changed
- **Docker Build Process:**
  - Enhanced `build-check` job in `ci-main.yml` to include security scanning of the backend image.
  - Updated `ci-main.yml` to fail on critical or high severity vulnerabilities (exit code 1).

### Infrastructure
- **Nginx Configuration:**
  - Implemented language detection based on `Accept-Language` header in `nginx-main.conf`.
  - Added root path redirect optimization in `site.conf.template` to handle language redirection at the Nginx level, reducing load on Django.

### Backend
- **Context Processors:**
  - Updated `site_settings` context processor to load settings from Redis (`SiteSettingsManager`) instead of direct database access, improving performance and potentially reducing attack surface on the DB.

### Documentation
- **Architecture:**
  - Updated `tech_stack.md` to include new security tools (`Pip-audit`, `Trivy`).
  - Updated CI/CD workflow documentation (`ci-develop.md`, `ci-main.md`, `workflows.md`) to reflect the addition of security scanning steps.
