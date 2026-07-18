#!/bin/sh
set -eu

DEPLOY_DIR="${DEPLOY_DIR:-/opt/lily_website/deploy}"
BACKUP_DIR="${BACKUP_DIR:-/opt/lily_website/backups}"
STATE_DIR="${STATE_DIR:-/opt/lily_website/state}"
VERSION="${VERSION:-manual}"
ENV_FILE="${ENV_FILE:-$DEPLOY_DIR/.env}"

mkdir -p "$BACKUP_DIR" "$STATE_DIR"
chmod 700 "$STATE_DIR"
cd "$DEPLOY_DIR"

DATABASE_URL="$(
  ENV_FILE="$ENV_FILE" python3 - <<'PY'
import os
from pathlib import Path

env_path = Path(os.environ["ENV_FILE"])
for raw_line in env_path.read_text().splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#") or not line.startswith("DATABASE_URL="):
        continue
    value = line.split("=", 1)[1].strip().strip("\"'")
    print(value)
    break
PY
)"

if [ -z "$DATABASE_URL" ]; then
  echo "DATABASE_URL not found in $ENV_FILE." >&2
  exit 1
fi

timestamp="$(date +%F_%H-%M)"
backup_file="$BACKUP_DIR/pre-manual-deploy-$VERSION-$timestamp.dump"
tmp_file="$BACKUP_DIR/tmp_backup.dump"

rm -f "$tmp_file"
echo "Creating pre-deploy database backup at $backup_file..."

case "$DATABASE_URL" in
  *"@db:"* | *"@db/"*)
    docker compose -f docker-compose.prod.yml up -d --wait db
    docker compose -f docker-compose.prod.yml exec -T db sh -ec \
      'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-acl -Fc -f /backups/tmp_backup.dump && pg_restore --list /backups/tmp_backup.dump >/dev/null'
    ;;
  *)
    docker run --rm \
      -e DATABASE_URL="$DATABASE_URL" \
      -v "$BACKUP_DIR:/backups" \
      postgres:16-alpine \
      sh -ec 'pg_dump "$DATABASE_URL" --no-owner --no-acl -Fc -f /backups/tmp_backup.dump && pg_restore --list /backups/tmp_backup.dump >/dev/null'
    ;;
esac

mv "$tmp_file" "$backup_file"
test -s "$backup_file"
cp "$ENV_FILE" "$STATE_DIR/.env.before-deploy"
cp "$DEPLOY_DIR/docker-compose.prod.yml" "$STATE_DIR/docker-compose.prod.before-deploy.yml"
chmod 600 "$STATE_DIR/.env.before-deploy"

echo "Database backup saved successfully: $backup_file"
