# 🌿 Git Flow & Branching Strategy

[⬅️ Back](../README.md) | [🏠 Docs Root](../../README.md)

We use a **Scoped Branching Strategy** combined with a 3-tier branch structure to ensure code stability and clear ownership in our monorepo.

## 🏷️ Branch Naming Convention (Scoped)

Since this is a monorepo, every branch **MUST** indicate which part of the system it affects.

**Format:** `type/scope/description`

### 1. Types
| Type | Description |
|:---|:---|
| `feature` | New functionality |
| `fix` | Bug fix |
| `refactor` | Code restructuring without behavior change |
| `chore` | Maintenance, dependency updates, config changes |
| `docs` | Documentation updates |
| `test` | Adding or fixing tests |

### 2. Scopes
| Scope | Path | Description |
|:---|:---|:---|
| `backend` | `src/lily_backend` | Server-side logic |
| `bot` | `src/telegram_bot` | Telegram Bot |
| `shared` | `src/shared` | Shared code (DTOs, Utils) |
| `infra` | `docker/`, `k8s/` | DevOps, Docker, CI/CD |
| `docs` | `docs/` | Global documentation |

### 3. Examples
*   ✅ `feature/bot/add-admin-menu`
*   ✅ `fix/backend/user-auth-error`
*   ✅ `chore/infra/update-docker-compose`
*   ✅ `docs/shared/update-api-contract`
*   ❌ `feature/add-login` (Missing scope)

---

## 🌳 Branch Structure

### 1. `develop` 🛠️ (Development)

*   **Purpose:** Main branch for integrating new features. Contains "fresh" but potentially unstable code.
*   **Rules:**
    *   All new features (`feature/*`) are merged here via Pull Request (PR).
    *   **CI Checks:** Linters run (`Ruff`, `Mypy`). Database tests are **not** run for speed.
*   **Protection:** Requires passing linters.

### 2. `main` 🧪 (Staging / Pre-Release)

*   **Purpose:** Stable branch ready for release. Acts as Staging environment.
*   **Rules:**
    *   Code enters here only from `develop` via PR.
    *   **CI Checks:** **Full test suite** runs (`Pytest` with DB) and Docker image build check.
*   **Protection:** Strict. Merge only if all tests pass. Direct push forbidden.

### 3. `release` 🚀 (Production)

*   **Purpose:** Code running on the production server.
*   **Rules:**
    *   Code enters here **only from `main`** via PR.
    *   **CD Action:** Pushing to this branch triggers automatic deployment to VPS.
*   **Protection:** Maximum. Merge allowed **only** from `main` branch (controlled by GitHub Actions).

---

## 🔄 Workflow

1.  **New Task:**
    *   Create branch from `develop`: `git checkout -b feature/bot/my-cool-feature develop`.
    *   Write code, commit.
    *   Run local check before push: `.\check_local.ps1` (Windows) or `pwsh` (Linux/Mac).

2.  **Integration (Develop):**
    *   Push and open PR to `develop`.
    *   GitHub Actions checks style and types.
    *   Merge PR.

3.  **Stabilization (Main):**
    *   When features are ready, open PR `develop` -> `main`.
    *   GitHub Actions runs heavy tests.
    *   If all OK — merge.

4.  **Release (Release):**
    *   Open PR `main` -> `release`.
    *   GitHub Actions verifies source is `main`.
    *   After merge, magic begins: Docker build -> Push to GHCR -> VPS Update.
