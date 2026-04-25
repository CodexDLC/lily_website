# ⚜️ Lily Beauty Salon

[🇷🇺 Русский](./README-RU.md) | [📖 Documentation Hub](https://codexdlc.github.io/lily_website/)

> **Web resource development for a beauty salon in Germany.**
>
> 🚀 **Status:** Active Development (Django + HTMX + Email Notifications + ARQ).

---

## 🎯 About the Project

The project is a professional business website for a premium beauty salon, featuring a public service catalog and an integrated appointment management system (CRM).

### Key Stages
1.  **Public Website (Landing)**:
    *   Presentation of top masters.
    *   Catalog of services, prices, portfolio.
    *   Trust factor: Integration of diplomas and certificates.
2.  **Automation**:
    *   Online booking system implementation.
    *   **"Time Tetris" Algorithm**: Smart calculation of free slots based on service duration.
3.  **Management (Cabinet)**:
    *   Personalized staff cabinet for schedule management.
    *   **Email Notifications**: Automated reminders for clients and status updates for staff.
    *   **Magic Login**: Secure, passwordless entry for staff via email.

### 🎨 Design Code
*   **Style:** Classic, Premium (Dark Luxury).
*   **Palette:** 🟢 Deep Emerald, 🟡 Gold, ⚪️ White.
*   **Accents:** Strict typography and plenty of "air".

---

## 🛠 Tech Stack

Built on a modular features-based architecture.

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | **Django 5.1** | Features-based architecture, Ninja API |
| **Notifications** | **Email (SMTP)** | Automated mailings and staff alerts |
| **Worker** | **ARQ** | Async task queue for background processes |
| **Frontend** | **HTML/CSS/JS** | Django Templates, HTMX, Vanilla JS |
| **Database** | **PostgreSQL** | Primary persistent storage |
| **Cache** | **Redis** | Caching, Session storage, Task queue |
| **Infra** | **Docker** | Docker Compose, Nginx, GitHub Actions |

---

## 🚀 Quick Start

### 1. Clone

```bash
git clone https://github.com/codexdlc/lily_website.git
cd lily_website
```

### 2. Install Dependencies

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
uv sync
```

### 3. Environment Setup

Create a `.env` file in the backend directory:
*   `src/lily_backend/.env`

### 4. Run (Local Development)

**Django:**
```bash
cd src/lily_backend
python manage.py migrate
python manage.py runserver
```

**Worker ARQ:**
```bash
# From project root
uv run arq src.workers.system_worker.worker.WorkerSettings
```

### 5. Python Path Configuration (Important!)

For correct module imports, add the project root to PYTHONPATH:

**Linux/macOS:**
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Windows (PowerShell):**
```powershell
$env:PYTHONPATH = "$env:PYTHONPATH;$PWD"
```

**PyCharm:**
1. Settings → Project → Project Structure
2. Mark the project root (`lily_website`) as "Source Root"

**VSCode:**

Create `.vscode/settings.json`:
```json
{
    "python.analysis.extraPaths": ["${workspaceFolder}"],
    "terminal.integrated.env.linux": {
        "PYTHONPATH": "${workspaceFolder}:${env:PYTHONPATH}"
    },
    "terminal.integrated.env.windows": {
        "PYTHONPATH": "${workspaceFolder};${env:PYTHONPATH}"
    }
}
```

**Running Tests:**
```bash
# From project root
uv run pytest
```

---

## 📂 Project Structure

```
lily_website/
├── src/
│   ├── lily_backend/         # Django backend
│   │   ├── system/           # Core system models (Client, etc.)
│   │   ├── cabinet/          # Staff cabinet views and services
│   │   ├── core/             # Project settings, URLs, logging
│   │   ├── features/         # Modular business logic (booking, etc.)
│   │   ├── static/           # Global static files
│   │   └── templates/        # Global HTML templates
│   └── workers/              # ARQ background workers
├── deploy/                   # Docker-compose and Nginx configs
├── docs/                     # Technical documentation & Roadmaps
└── pyproject.toml            # uv, Hatchling, Ruff, Mypy configs
```

---

## 🔧 Development Tools

```bash
# Linting and formatting
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy src/

# Tests
uv run pytest
```

---

© 2026 Lily Beauty Salon. Developed by CodexDLC.
