# Local PostgreSQL migration and backups

## Target layout

- Local Docker PostgreSQL is the application primary.
- The original Neon database remains unchanged during the rollback window.
- A separate Neon database or branch can be enabled as a mutable warm copy.
- Hetzner Object Storage keeps encrypted, timestamped dump history.
- The VPS keeps the most recent 14 days of unencrypted dumps for fast recovery.

## Required environment

Add the values from `.env.example` to the production `ENV_FILE` GitHub secret.
Use a long, unique `POSTGRES_PASSWORD` and `BACKUP_ENCRYPTION_PASSWORD`. Keep the
encryption password out of Object Storage and keep an independent recovery copy
outside the VPS.

Create a dedicated Hetzner Object Storage access key and restrict it to
`lily-postgres-backups` with a bucket policy. Hetzner keys can access all
buckets in their project by default. Then set:

```dotenv
BACKUP_S3_ENABLED=True
BACKUP_S3_BUCKET=lily-postgres-backups
BACKUP_S3_ENDPOINT=https://nbg1.your-objectstorage.com
BACKUP_S3_REGION=nbg1
BACKUP_S3_PREFIX=postgres
BACKUP_S3_ACCESS_KEY_ID=...
BACKUP_S3_SECRET_ACCESS_KEY=...
BACKUP_ENCRYPTION_PASSWORD=...
```

Keep `ENABLE_NEON_WARM_SYNC=False` for the initial cutover. When the local
database has been stable for the chosen rollback period, use a separate Neon
branch/database as `BACKUP_NEON_DATABASE_URL` and enable the sync. The scripts
refuse to overwrite `LEGACY_DATABASE_URL` unless a second explicit override is
provided.

## One-time cutover

1. Update the production `ENV_FILE` secret with both the local `DATABASE_URL`
   and the old Neon `LEGACY_DATABASE_URL`.
2. Run `Deploy Production (Manual)` with mode `cutover_local_database`.
3. Select the explicit cutover confirmation.
4. Check `/opt/lily_website/state/local-db-ready` on the VPS.
5. Verify the application and a new booking before considering the cutover
   complete.

Normal manual deployments refuse to start until the cutover marker exists.
On a cutover failure, the script restores the previous environment and Compose
configuration and attempts to restart the old deployment.

## Object Storage policy

Enable bucket versioning and configure lifecycle retention in the Hetzner
console. Use unique timestamped keys even with versioning enabled. If immutable
Object Lock is required and was not selected when the bucket was created,
recreate the backup bucket with Object Lock enabled before production use.

## Recovery check

List an object key in the bucket, then download, decrypt, and validate it:

```sh
sh scripts/download_backup_from_s3.sh \
  postgres/YYYY/MM/local-postgres-YYYY-MM-DD_HH-MM-SS.dump.enc
```

The command validates the encrypted SHA-256 sidecar and the decrypted PostgreSQL
archive. To restore it into local PostgreSQL:

```sh
CONFIRM_LOCAL_DB_RESTORE=1 \
  sh scripts/restore_local_postgres.sh \
  local-postgres-YYYY-MM-DD_HH-MM-SS.dump
```

The restore command stops application writers and creates another local dump
before replacing the database.
