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

BACKUP_S3_ENABLED="$(read_env_value BACKUP_S3_ENABLED)"
if [ "$BACKUP_S3_ENABLED" != "True" ]; then
  echo "Hetzner S3 backup is disabled; set BACKUP_S3_ENABLED=True to enable it."
  exit 0
fi

if [ "$#" -eq 1 ]; then
  backup_name="$(basename "$1")"
else
  backup_name="$(find "$BACKUP_DIR" -name "local-postgres-*.dump" -type f -printf "%T@ %f\n" | sort -nr | awk 'NR==1 {print $2}')"
fi

if [ -z "$backup_name" ] || [ ! -f "$BACKUP_DIR/$backup_name" ]; then
  echo "Postgres dump was not found under $BACKUP_DIR." >&2
  exit 1
fi

BACKUP_S3_BUCKET="$(read_env_value BACKUP_S3_BUCKET)"
BACKUP_S3_ENDPOINT="$(read_env_value BACKUP_S3_ENDPOINT)"
BACKUP_S3_REGION="$(read_env_value BACKUP_S3_REGION)"
BACKUP_S3_PREFIX="$(read_env_value BACKUP_S3_PREFIX)"
BACKUP_S3_ACCESS_KEY_ID="$(read_env_value BACKUP_S3_ACCESS_KEY_ID)"
BACKUP_S3_SECRET_ACCESS_KEY="$(read_env_value BACKUP_S3_SECRET_ACCESS_KEY)"
BACKUP_ENCRYPTION_PASSWORD="$(read_env_value BACKUP_ENCRYPTION_PASSWORD)"
BACKUP_AWS_CLI_IMAGE="$(read_env_value BACKUP_AWS_CLI_IMAGE)"
BACKUP_AWS_CLI_IMAGE="${BACKUP_AWS_CLI_IMAGE:-amazon/aws-cli:2}"

require_value() {
  name="$1"
  value="$2"
  if [ -z "$value" ]; then
    echo "$name is required when S3 backup is enabled." >&2
    exit 1
  fi
}

require_value BACKUP_S3_BUCKET "$BACKUP_S3_BUCKET"
require_value BACKUP_S3_ENDPOINT "$BACKUP_S3_ENDPOINT"
require_value BACKUP_S3_REGION "$BACKUP_S3_REGION"
require_value BACKUP_S3_ACCESS_KEY_ID "$BACKUP_S3_ACCESS_KEY_ID"
require_value BACKUP_S3_SECRET_ACCESS_KEY "$BACKUP_S3_SECRET_ACCESS_KEY"
require_value BACKUP_ENCRYPTION_PASSWORD "$BACKUP_ENCRYPTION_PASSWORD"

command -v openssl >/dev/null 2>&1 || {
  echo "openssl is required for backup encryption." >&2
  exit 1
}

backup_path="$BACKUP_DIR/$backup_name"
encrypted_name="$backup_name.enc"
encrypted_path="$BACKUP_DIR/.$encrypted_name.tmp"
checksum_path="$BACKUP_DIR/.$encrypted_name.sha256.tmp"
cleanup() {
  rm -f "$encrypted_path" "$checksum_path"
}
trap cleanup EXIT HUP INT TERM

export BACKUP_ENCRYPTION_PASSWORD
openssl enc -aes-256-cbc -salt -pbkdf2 -iter 200000 \
  -in "$backup_path" \
  -out "$encrypted_path" \
  -pass env:BACKUP_ENCRYPTION_PASSWORD

checksum="$(sha256sum "$encrypted_path" | awk '{print $1}')"
printf '%s  %s\n' "$checksum" "$encrypted_name" >"$checksum_path"

prefix="$(printf '%s' "$BACKUP_S3_PREFIX" | sed 's|^/*||; s|/*$||')"
date_path="$(date +%Y/%m)"
if [ -n "$prefix" ]; then
  object_key="$prefix/$date_path/$encrypted_name"
else
  object_key="$date_path/$encrypted_name"
fi

aws_cli() {
  docker run --rm \
    -e AWS_ACCESS_KEY_ID="$BACKUP_S3_ACCESS_KEY_ID" \
    -e AWS_SECRET_ACCESS_KEY="$BACKUP_S3_SECRET_ACCESS_KEY" \
    -e AWS_DEFAULT_REGION="$BACKUP_S3_REGION" \
    -v "$BACKUP_DIR:/backups:ro" \
    "$BACKUP_AWS_CLI_IMAGE" \
    --endpoint-url "$BACKUP_S3_ENDPOINT" "$@"
}

echo "Uploading encrypted backup to s3://$BACKUP_S3_BUCKET/$object_key..."
aws_cli s3 cp "/backups/$(basename "$encrypted_path")" \
  "s3://$BACKUP_S3_BUCKET/$object_key" \
  --only-show-errors \
  --metadata "sha256=$checksum"
aws_cli s3 cp "/backups/$(basename "$checksum_path")" \
  "s3://$BACKUP_S3_BUCKET/$object_key.sha256" \
  --only-show-errors

remote_size="$(
  aws_cli s3api head-object \
    --bucket "$BACKUP_S3_BUCKET" \
    --key "$object_key" \
    --query ContentLength \
    --output text
)"
case "$remote_size" in
  "" | *[!0-9]*)
    echo "Uploaded S3 object returned an invalid size: $remote_size" >&2
    exit 1
    ;;
esac
if [ "$remote_size" -le 0 ]; then
  echo "Uploaded S3 object is empty or could not be verified." >&2
  exit 1
fi

echo "Encrypted S3 backup verified: $object_key ($remote_size bytes, sha256 $checksum)"
