# ⚜️ Lily Beauty Salon

[🇷🇺 Русский](./README-RU.md)

> **Premium web resource development for a beauty salon in Germany.**
>
> 🚀 **Status:** Active Development (Django + Telegram Bot).

---

## 🎯 About the Project

The project is an image showcase site transforming into a full-featured appointment management system (CRM).

### Key Stages
1.  **Showcase (MVP)**:
    *   Presentation of top masters (Liliia Yakina).
    *   Catalog of services, prices, portfolio.
    *   Trust factor: Integration of diplomas and certificates.
2.  **Automation**:
    *   Online booking system implementation.
    *   **"Time Tetris" Algorithm**: Smart calculation of free slots based on service duration.
3.  **Management (Telegram Bot)**:
    *   Instant notifications for staff about new bookings.
    *   Schedule management via messenger.

### 🎨 Design Code
*   **Style:** Classic, Premium (Dark Luxury).
*   **Palette:** 🟢 Deep Emerald, 🟡 Gold, ⚪️ White.
*   **Accents:** Strict typography and plenty of "air".

---

## 🛠 Tech Stack

Built on a modular monorepo structure (Django + Aiogram).

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | **Django 5.1** | Features-based architecture, Split settings |
| **Bot** | **Aiogram 3.x** | Async bot, DB integration |
| **Frontend** | **HTML/CSS/JS** | Django Templates, Vanilla JS |
| **Database** | **PostgreSQL** | Schema isolation (`django_app`, `bot_app`) |
| **Infra** | **Docker** | Docker Compose, Nginx, GitHub Actions |

---

## 🚀 Quick Start

### 1. Clone

```bash
git clone https://github.com/codexdlc/lily_website.git
cd lily_website
```

### 2. Install Dependencies

Using [Poetry](https://python-poetry.org/) for dependency management.

```bash
pip install poetry
poetry config virtualenvs.in-project true
poetry install --extras "django bot dev"
```

### 3. Environment Setup

Create `.env` files in component directories:
*   `src/backend-django/.env`
*   `src/telegram_bot/.env`

### 4. Run (Local Development)

**Django:**
```bash
cd src/backend_django
python manage.py migrate
python manage.py runserver
```

**Telegram Bot:**
```bash
python -m src.telegram_bot.app_telegram
```

**Worker ARQ:**
```bash
arq src.workers.notification_worker.worker.WorkerSettings
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
pytest src/
```

---

## 📂 Project Structure

```
lily_website/
├── src/
│   ├── backend-django/       # Django backend (features-based structure)
│   │   ├── core/             # Settings, urls
│   │   ├── features/         # Business logic (main, system, etc.)
│   │   ├── static/           # Static files (CSS, JS, IMG)
│   │   └── templates/        # HTML templates
│   ├── telegram_bot/         # Telegram Bot (aiogram 3.x)
│   └── shared/               # Shared code
├── deploy/                   # Docker-compose and Nginx configs
├── docs/                     # Technical documentation
├── 1/arch/                   # Architectural documentation and concepts
└── pyproject.toml            # Poetry, Ruff, Mypy configs
```

---

## 🔧 Development Tools

```bash
# Linting and formatting
ruff check src/
ruff format src/

# Type checking
mypy src/

# Tests
pytest
```

---

© 2026 Lily Beauty Salon. Developed by CodexDLC.
