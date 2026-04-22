# 🛠️ Technology Stack

[⬅️ Back](./README.md) | [🏠 Docs Root](../../README.md)

## 🌐 Core Stack

| Domain | Technology | Version | Purpose |
|:---|:---|:---|:---|
| **Language** | Python | 3.13 | Core language for all backend services |
| **Framework** | Django | 5.1 | Web framework, ORM, Admin panel |
| **API** | Django Ninja | 1.x | Fast, typed API endpoints |
| **Bot** | Aiogram | 3.x | Asynchronous Telegram Bot framework |
| **Worker** | ARQ | 0.27+ | Async job queue (Redis-based) |
| **Database** | PostgreSQL | 16 | Primary relational database |
| **Cache** | Redis | 7 | Caching, sessions, task queue |

## 🛡️ Quality Assurance (Zero-Trust Infrastructure)

We employ a multi-layered approach to ensure code quality and security.

### 1. Local Pre-commit (First Barrier)
*   **Ruff:** Fast Python linter and formatter. Enforces code style (PEP 8) and catches common errors.
*   **Mypy:** Static type checker. Ensures type safety across the codebase.
*   **Bandit:** Security linter. Scans for common security issues in Python code.
*   **Detect Secrets:** Prevents committing secrets (API keys, passwords) to git.
*   **Pip-audit:** Checks for known vulnerabilities in Python dependencies.

### 2. CI Development (Shift-Left)
*   **Trigger:** Push to `develop`.
*   **Actions:**
    *   **Linting:** Ruff + Mypy.
    *   **Security:** Trivy FS Scan (scans file system for vulnerabilities and secrets).

### 3. CI Main (Integration & Build)
*   **Trigger:** PR to `main`.
*   **Actions:**
    *   **Tests:** Pytest (Unit + Integration).
    *   **Build:** Docker Build verification.
    *   **Security:** Trivy Image Scan (scans built Docker images for OS/Library vulnerabilities).
    *   **Integration:** Full stack test via `docker compose` validation (Backend + DB + Redis + Bot).

### 4. CD Production (Secure Deployment)
*   **Trigger:** Tag push (`v*`).
*   **Process:** Builds images, pushes to GHCR, and deploys to production via SSH.
*   **Security:** Uses GitHub Secrets for all sensitive data.

## 🎨 Frontend

*   **Templates:** Django Templates (DTL)
*   **Interactivity:** HTMX (for dynamic content without full SPA complexity)
*   **Styling:** CSS (Custom design system)
*   **JS:** Vanilla JavaScript (minimal dependencies)

## 🐳 Infrastructure

*   **Containerization:** Docker & Docker Compose
*   **Web Server:** Nginx (Reverse proxy, SSL termination, static files)
*   **CI/CD:** GitHub Actions
