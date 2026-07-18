#!/bin/sh
set -eu

deploy_dir="${DEPLOY_DIR:-/opt/lily_website/deploy}"
systemd_dir="${SYSTEMD_DIR:-/etc/systemd/system}"

if ! command -v systemctl >/dev/null 2>&1; then
  echo "systemctl is not available on this host; skipping timer installation." >&2
  exit 0
fi

if [ "$(id -u)" -eq 0 ]; then
  sudo_cmd=""
elif command -v sudo >/dev/null 2>&1; then
  sudo_cmd="sudo"
else
  echo "Root privileges or sudo are required to install the backup timer." >&2
  exit 1
fi

$sudo_cmd install -m 0644 "$deploy_dir/systemd/lily-postgres-backup.service" "$systemd_dir/lily-postgres-backup.service"
$sudo_cmd install -m 0644 "$deploy_dir/systemd/lily-postgres-backup.timer" "$systemd_dir/lily-postgres-backup.timer"

$sudo_cmd systemctl daemon-reload
$sudo_cmd systemctl enable --now lily-postgres-backup.timer
$sudo_cmd systemctl list-timers lily-postgres-backup.timer --no-pager
