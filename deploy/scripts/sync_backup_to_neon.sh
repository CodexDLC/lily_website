#!/bin/sh
set -eu

DEPLOY_DIR="${DEPLOY_DIR:-/opt/lily_website/deploy}"
BACKUP_DIR="${BACKUP_DIR:-/opt/lily_website/backups}"
ENV_FILE="${ENV_FILE:-$DEPLOY_DIR/.env}"

ENABLE_NEON_WARM_SYNC="$(
  ENV_FILE="$ENV_FILE" python3 - <<'PY'
import os
from pathlib import Path

env_path = Path(os.environ["ENV_FILE"])
for raw_line in env_path.read_text().splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#") or not line.startswith("ENABLE_NEON_WARM_SYNC="):
        continue
    print(line.split("=", 1)[1].strip().strip("\"'"))
    break
PY
)"

if [ "$ENABLE_NEON_WARM_SYNC" != "True" ]; then
  echo "Neon warm sync is disabled; set ENABLE_NEON_WARM_SYNC=True to enable it."
  exit 0
fi

if [ "${CONFIRM_NEON_RESTORE:-}" != "1" ]; then
  echo "Refusing to overwrite Neon backup target. Set CONFIRM_NEON_RESTORE=1 to continue." >&2
  exit 2
fi

if [ "$#" -eq 1 ]; then
  backup_name="$(basename "$1")"
else
  backup_name="$(find "$BACKUP_DIR" -name "local-postgres-*.dump" -type f -printf "%T@ %f\n" | sort -nr | awk 'NR==1 {print $2}')"
fi

if [ -z "$backup_name" ]; then
  echo "No local-postgres dump found under $BACKUP_DIR." >&2
  exit 1
fi

backup_path="$BACKUP_DIR/$backup_name"
if [ ! -f "$backup_path" ]; then
  echo "Backup file not found under $BACKUP_DIR: $backup_name" >&2
  exit 1
fi

BACKUP_NEON_DATABASE_URL="$(
  ENV_FILE="$ENV_FILE" python3 - <<'PY'
import os
from pathlib import Path

env_path = Path(os.environ["ENV_FILE"])
for raw_line in env_path.read_text().splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#") or not line.startswith("BACKUP_NEON_DATABASE_URL="):
        continue
    value = line.split("=", 1)[1].strip().strip("\"'")
    print(value)
    break
PY
)"

if [ -z "$BACKUP_NEON_DATABASE_URL" ]; then
  echo "BACKUP_NEON_DATABASE_URL not found in $ENV_FILE." >&2
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

if [ "$BACKUP_NEON_DATABASE_URL" = "$LEGACY_DATABASE_URL" ] && [ "${ALLOW_OVERWRITE_LEGACY_NEON:-}" != "1" ]; then
  echo "Refusing to overwrite the legacy Neon rollback database." >&2
  echo "Use a separate Neon branch/database, or set ALLOW_OVERWRITE_LEGACY_NEON=1 explicitly." >&2
  exit 2
fi

echo "Validating dump before Neon sync: $backup_path"
docker run --rm \
  -v "$BACKUP_DIR:/backups:ro" \
  postgres:16-alpine \
  pg_restore --list "/backups/$backup_name" >/dev/null

echo "Restoring $backup_name into Neon backup target..."
docker run --rm \
  -e BACKUP_NEON_DATABASE_URL="$BACKUP_NEON_DATABASE_URL" \
  -v "$BACKUP_DIR:/backups:ro" \
  postgres:16-alpine \
  sh -ec 'pg_restore --exit-on-error --clean --if-exists --no-owner --no-acl -d "$BACKUP_NEON_DATABASE_URL" "/backups/'"$backup_name"'"'

echo "Validating Neon warm target..."
docker run --rm \
  -e BACKUP_NEON_DATABASE_URL="$BACKUP_NEON_DATABASE_URL" \
  postgres:16-alpine \
  sh -ec 'test "$(psql "$BACKUP_NEON_DATABASE_URL" -Atqc "SELECT count(*) FROM django_migrations")" -gt 0'

echo "Neon backup target synchronized from: $backup_path"
