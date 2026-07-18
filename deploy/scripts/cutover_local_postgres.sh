#!/bin/sh
set -eu

DEPLOY_DIR="${DEPLOY_DIR:-/opt/lily_website/deploy}"
BACKUP_DIR="${BACKUP_DIR:-/opt/lily_website/backups}"
STATE_DIR="${STATE_DIR:-/opt/lily_website/state}"
ENV_FILE="${ENV_FILE:-$DEPLOY_DIR/.env}"
READY_MARKER="$STATE_DIR/local-db-ready"
ROLLBACK_ENV="$STATE_DIR/.env.before-deploy"
ROLLBACK_COMPOSE="$STATE_DIR/docker-compose.prod.before-deploy.yml"

if [ "${CONFIRM_LOCAL_DB_CUTOVER:-}" != "1" ]; then
  echo "Refusing local database cutover without CONFIRM_LOCAL_DB_CUTOVER=1." >&2
  exit 2
fi

if [ -f "$READY_MARKER" ]; then
  echo "Local database cutover has already completed: $READY_MARKER" >&2
  exit 2
fi

if [ ! -s "$ROLLBACK_ENV" ] || [ ! -s "$ROLLBACK_COMPOSE" ]; then
  echo "Rollback configuration is missing under $STATE_DIR." >&2
  exit 1
fi

LEGACY_DATABASE_URL="$(
  ENV_FILE="$ENV_FILE" python3 - <<'PY'
import os
from pathlib import Path

env_path = Path(os.environ["ENV_FILE"])
for raw_line in env_path.read_text().splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#") or not line.startswith("LEGACY_DATABASE_URL="):
        continue
    print(line.split("=", 1)[1].strip().strip("\"'"))
    break
PY
)"

if [ -z "$LEGACY_DATABASE_URL" ]; then
  echo "LEGACY_DATABASE_URL not found in $ENV_FILE." >&2
  exit 1
fi

rollback() {
  exit_code=$?
  trap - EXIT HUP INT TERM
  echo "Cutover failed; restoring the previous deployment configuration." >&2
  cd "$DEPLOY_DIR"
  docker compose -f docker-compose.prod.yml stop backend worker system_worker nginx db 2>/dev/null || true
  cp "$ROLLBACK_ENV" "$DEPLOY_DIR/.env"
  cp "$ROLLBACK_COMPOSE" "$DEPLOY_DIR/docker-compose.prod.yml"
  docker compose -f docker-compose.prod.yml up -d --wait || true
  exit "$exit_code"
}
trap rollback EXIT HUP INT TERM

mkdir -p "$BACKUP_DIR" "$STATE_DIR"
chmod 700 "$STATE_DIR"
cd "$DEPLOY_DIR"

echo "Stopping application writers before the final Neon snapshot..."
docker compose -f docker-compose.prod.yml stop backend worker system_worker

timestamp="$(date +%F_%H-%M-%S)"
backup_name="cutover-final-$timestamp.dump"
backup_path="$BACKUP_DIR/$backup_name"
tmp_path="$BACKUP_DIR/tmp_cutover_backup.dump"
rm -f "$tmp_path"

echo "Creating the final Neon snapshot..."
docker run --rm \
  -e LEGACY_DATABASE_URL="$LEGACY_DATABASE_URL" \
  -v "$BACKUP_DIR:/backups" \
  postgres:17-alpine \
  sh -ec 'pg_dump "$LEGACY_DATABASE_URL" --no-owner --no-acl -Fc -f /backups/tmp_cutover_backup.dump && pg_restore --list /backups/tmp_cutover_backup.dump >/dev/null'
mv "$tmp_path" "$backup_path"
test -s "$backup_path"

docker compose -f docker-compose.prod.yml up -d --wait db redis
table_count="$(
  docker compose -f docker-compose.prod.yml exec -T db sh -ec \
    'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atqc "SELECT count(*) FROM pg_tables WHERE schemaname = '\''public'\''"'
)"
if [ "$table_count" -ne 0 ]; then
  echo "Refusing cutover: local PostgreSQL is not empty ($table_count public tables)." >&2
  exit 1
fi

echo "Restoring the final snapshot into local PostgreSQL..."
docker compose -f docker-compose.prod.yml exec -T db sh -ec \
  'pg_restore --exit-on-error --no-owner --no-acl -U "$POSTGRES_USER" -d "$POSTGRES_DB" "/backups/'"$backup_name"'"'
sh "$DEPLOY_DIR/scripts/verify_local_postgres.sh"

docker compose -f docker-compose.prod.yml run --rm -T backend python manage.py migrate --noinput
docker compose -f docker-compose.prod.yml run --rm -T backend python manage.py collectstatic --noinput
docker compose -f docker-compose.prod.yml up -d --wait backend worker system_worker nginx

checksum="$(sha256sum "$backup_path" | awk '{print $1}')"
{
  echo "completed_at=$timestamp"
  echo "source_backup=$backup_name"
  echo "sha256=$checksum"
} >"$READY_MARKER"
chmod 600 "$READY_MARKER"

trap - EXIT HUP INT TERM
echo "Local PostgreSQL cutover completed and verified."
