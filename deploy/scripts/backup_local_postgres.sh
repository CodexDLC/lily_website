#!/bin/sh
set -eu

DEPLOY_DIR="${DEPLOY_DIR:-/opt/lily_website/deploy}"
BACKUP_DIR="${BACKUP_DIR:-/opt/lily_website/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

mkdir -p "$BACKUP_DIR"
cd "$DEPLOY_DIR"

timestamp="$(date +%F_%H-%M-%S)"
backup_file="$BACKUP_DIR/local-postgres-$timestamp.dump"
tmp_file="$BACKUP_DIR/tmp_local_backup.dump"

rm -f "$tmp_file"
echo "Creating local Postgres backup at $backup_file..."

docker compose -f docker-compose.prod.yml up -d --wait db
docker compose -f docker-compose.prod.yml exec -T db sh -ec \
  'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-acl -Fc -f /backups/tmp_local_backup.dump && pg_restore --list /backups/tmp_local_backup.dump >/dev/null'

mv "$tmp_file" "$backup_file"
test -s "$backup_file"

find "$BACKUP_DIR" -name "local-postgres-*.dump" -mtime +"$RETENTION_DAYS" -delete

echo "Local Postgres backup saved successfully: $backup_file"
