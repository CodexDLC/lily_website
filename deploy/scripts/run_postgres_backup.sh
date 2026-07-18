#!/bin/sh
set -eu

DEPLOY_DIR="${DEPLOY_DIR:-/opt/lily_website/deploy}"
BACKUP_DIR="${BACKUP_DIR:-/opt/lily_website/backups}"
ENV_FILE="${ENV_FILE:-$DEPLOY_DIR/.env}"

read_env_value() {
  ENV_FILE="$ENV_FILE" ENV_KEY="$1" python3 - <<'PY'
import os
from pathlib import Path

env_path = Path(os.environ["ENV_FILE"])
key = os.environ["ENV_KEY"]
for raw_line in env_path.read_text().splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#") or not line.startswith(f"{key}="):
        continue
    print(line.split("=", 1)[1].strip().strip("\"'"))
    break
PY
}

healthcheck_url="$(read_env_value BACKUP_HEALTHCHECK_URL)"
notify_failure() {
  exit_code=$?
  trap - EXIT HUP INT TERM
  if [ -n "$healthcheck_url" ]; then
    curl -fsS -m 15 "$healthcheck_url/fail" >/dev/null 2>&1 || true
  fi
  exit "$exit_code"
}
trap notify_failure EXIT HUP INT TERM

sh "$DEPLOY_DIR/scripts/backup_local_postgres.sh"
latest_backup="$(find "$BACKUP_DIR" -name "local-postgres-*.dump" -type f -printf "%T@ %p\n" | sort -nr | awk 'NR==1 {$1=""; sub(/^ /, ""); print}')"

if [ -z "$latest_backup" ]; then
  echo "The local Postgres backup completed without producing a dump." >&2
  exit 1
fi

sh "$DEPLOY_DIR/scripts/upload_backup_to_s3.sh" "$latest_backup"
CONFIRM_NEON_RESTORE=1 sh "$DEPLOY_DIR/scripts/sync_backup_to_neon.sh" "$latest_backup"

if [ -n "$healthcheck_url" ]; then
  curl -fsS -m 15 "$healthcheck_url" >/dev/null
fi

trap - EXIT HUP INT TERM
echo "Postgres backup pipeline completed: $latest_backup"
