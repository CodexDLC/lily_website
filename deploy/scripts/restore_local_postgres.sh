#!/bin/sh
set -eu

DEPLOY_DIR="${DEPLOY_DIR:-/opt/lily_website/deploy}"
BACKUP_DIR="${BACKUP_DIR:-/opt/lily_website/backups}"

if [ "${CONFIRM_LOCAL_DB_RESTORE:-}" != "1" ]; then
  echo "Refusing local restore without CONFIRM_LOCAL_DB_RESTORE=1." >&2
  exit 2
fi

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <backup-file-name-or-absolute-path>" >&2
  exit 2
fi

input="$1"
backup_name="$(basename "$input")"
backup_path="$BACKUP_DIR/$backup_name"

if [ ! -f "$backup_path" ]; then
  echo "Backup file not found under $BACKUP_DIR: $backup_name" >&2
  exit 1
fi

cd "$DEPLOY_DIR"

echo "Starting local Postgres container..."
docker compose -f docker-compose.prod.yml up -d --wait db

echo "Stopping application writers and preserving the current local database..."
docker compose -f docker-compose.prod.yml stop backend worker system_worker
sh "$DEPLOY_DIR/scripts/backup_local_postgres.sh"

echo "Validating dump: $backup_path"
docker compose -f docker-compose.prod.yml exec -T db pg_restore --list "/backups/$backup_name" >/dev/null

echo "Restoring dump into local Postgres database..."
docker compose -f docker-compose.prod.yml exec -T db sh -ec \
  'pg_restore --exit-on-error --clean --if-exists --no-owner --no-acl -U "$POSTGRES_USER" -d "$POSTGRES_DB" "/backups/'"$backup_name"'"'

sh "$DEPLOY_DIR/scripts/verify_local_postgres.sh"
docker compose -f docker-compose.prod.yml up -d --wait backend worker system_worker nginx
echo "Restore completed."
