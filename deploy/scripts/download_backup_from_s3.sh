#!/bin/sh
set -eu

DEPLOY_DIR="${DEPLOY_DIR:-/opt/lily_website/deploy}"
BACKUP_DIR="${BACKUP_DIR:-/opt/lily_website/backups}"
ENV_FILE="${ENV_FILE:-$DEPLOY_DIR/.env}"

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <object-key-ending-in-.dump.enc>" >&2
  exit 2
fi

object_key="$1"
encrypted_name="$(basename "$object_key")"
case "$encrypted_name" in
  *.dump.enc) ;;
  *)
    echo "Object key must end in .dump.enc." >&2
    exit 2
    ;;
esac

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

BACKUP_S3_BUCKET="$(read_env_value BACKUP_S3_BUCKET)"
BACKUP_S3_ENDPOINT="$(read_env_value BACKUP_S3_ENDPOINT)"
BACKUP_S3_REGION="$(read_env_value BACKUP_S3_REGION)"
BACKUP_S3_ACCESS_KEY_ID="$(read_env_value BACKUP_S3_ACCESS_KEY_ID)"
BACKUP_S3_SECRET_ACCESS_KEY="$(read_env_value BACKUP_S3_SECRET_ACCESS_KEY)"
BACKUP_ENCRYPTION_PASSWORD="$(read_env_value BACKUP_ENCRYPTION_PASSWORD)"
BACKUP_AWS_CLI_IMAGE="$(read_env_value BACKUP_AWS_CLI_IMAGE)"
BACKUP_AWS_CLI_IMAGE="${BACKUP_AWS_CLI_IMAGE:-amazon/aws-cli:2}"

require_value() {
  name="$1"
  value="$2"
  if [ -z "$value" ]; then
    echo "$name is required for S3 restore." >&2
    exit 1
  fi
}

require_value BACKUP_S3_BUCKET "$BACKUP_S3_BUCKET"
require_value BACKUP_S3_ENDPOINT "$BACKUP_S3_ENDPOINT"
require_value BACKUP_S3_REGION "$BACKUP_S3_REGION"
require_value BACKUP_S3_ACCESS_KEY_ID "$BACKUP_S3_ACCESS_KEY_ID"
require_value BACKUP_S3_SECRET_ACCESS_KEY "$BACKUP_S3_SECRET_ACCESS_KEY"
require_value BACKUP_ENCRYPTION_PASSWORD "$BACKUP_ENCRYPTION_PASSWORD"

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
encrypted_path="$BACKUP_DIR/$encrypted_name"
checksum_path="$encrypted_path.sha256"
dump_path="${encrypted_path%.enc}"

if [ -e "$encrypted_path" ] || [ -e "$checksum_path" ] || [ -e "$dump_path" ]; then
  echo "Refusing to overwrite an existing restore file under $BACKUP_DIR." >&2
  exit 1
fi

cleanup() {
  rm -f "$encrypted_path" "$checksum_path"
}
trap cleanup EXIT HUP INT TERM

aws_cli() {
  docker run --rm \
    -e AWS_ACCESS_KEY_ID="$BACKUP_S3_ACCESS_KEY_ID" \
    -e AWS_SECRET_ACCESS_KEY="$BACKUP_S3_SECRET_ACCESS_KEY" \
    -e AWS_DEFAULT_REGION="$BACKUP_S3_REGION" \
    -v "$BACKUP_DIR:/backups" \
    "$BACKUP_AWS_CLI_IMAGE" \
    --endpoint-url "$BACKUP_S3_ENDPOINT" "$@"
}

aws_cli s3 cp "s3://$BACKUP_S3_BUCKET/$object_key" "/backups/$encrypted_name" --only-show-errors
aws_cli s3 cp "s3://$BACKUP_S3_BUCKET/$object_key.sha256" "/backups/$encrypted_name.sha256" --only-show-errors

(
  cd "$BACKUP_DIR"
  sha256sum -c "$encrypted_name.sha256"
)

export BACKUP_ENCRYPTION_PASSWORD
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 \
  -in "$encrypted_path" \
  -out "$dump_path" \
  -pass env:BACKUP_ENCRYPTION_PASSWORD

docker run --rm \
  -v "$BACKUP_DIR:/backups:ro" \
  postgres:16-alpine \
  pg_restore --list "/backups/$(basename "$dump_path")" >/dev/null

trap - EXIT HUP INT TERM
rm -f "$encrypted_path" "$checksum_path"
echo "Downloaded, decrypted, and validated: $dump_path"
