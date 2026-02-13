# Worker Refactoring & Docker Configuration Changes

## 1. Worker Structure
- **Moved:** `src/telegram_bot/workers/notification_worker` -> `src/workers/notification_worker`.
- **Reason:** Separation of concerns. Workers are standalone processes, not part of the bot codebase.

## 2. Dockerfile (`deploy/worker/Dockerfile`)
- **Updated Path:** `CMD` now points to `src.workers.notification_worker.worker`.
- **Updated Copy:**
  - Removed `src/worker_arq` (old path).
  - Added `COPY src/workers /app/src/workers`.
  - Removed `src/backend_django` (worker uses API/Redis, not direct DB access).
  - Removed `src/telegram_bot` (worker uses shared config, not bot code).
- **Added README.md:** Added `COPY README.md ./` to all Dockerfiles (bot, worker, backend) because `pyproject.toml` requires it for package metadata generation during `pip install`.
- **Fixed Build Error:** Added `COPY src ./src` in the builder stage for all Dockerfiles (bot, worker, backend). This is required because `pip install .` needs the source code to build the package defined in `pyproject.toml`.

## 3. Docker Compose (`deploy/docker-compose.yml`) - Local
- **Updated Volumes:**
  - `../src/workers:/app/src/workers:ro` (instead of `worker_arq` or `telegram_bot`).
  - `../src/shared:/app/src/shared:ro`.
- **Updated Command:** Explicitly set command to run `notification_worker`.

## 4. Docker Compose Prod (`deploy/docker-compose.prod.yml`)
- **Added Backend:** Added `backend` service (was missing).
- **Updated Images:** Uses `${DOCKER_IMAGE_WORKER}`, `${DOCKER_IMAGE_BACKEND}`, etc.
- **Production Settings:**
  - No volumes for code (uses baked images).
  - `gunicorn` for backend.
  - `restart: always`.

## 5. Shared Configuration
- **Redis Streams:** Moved stream settings from `BotSettings` to `CommonSettings` (`src/shared/core/config.py`).
- **Constants:** Created `src/shared/core/constants.py` for `RedisStreams` constants.
- **Redis Service:** Refactored `RedisService` and `StreamManager` in `src/shared` to be used by both Bot and Worker.

## 6. Project Configuration (`pyproject.toml`)
- **Removed:** `package-mode = false` (to allow building as a package).
