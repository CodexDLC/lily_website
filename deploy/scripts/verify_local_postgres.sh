#!/bin/sh
set -eu

DEPLOY_DIR="${DEPLOY_DIR:-/opt/lily_website/deploy}"

cd "$DEPLOY_DIR"
docker compose -f docker-compose.prod.yml up -d --wait db

table_count="$(
  docker compose -f docker-compose.prod.yml exec -T db sh -ec \
    'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atqc "SELECT count(*) FROM pg_tables WHERE schemaname = '\''public'\''"'
)"

has_migrations="$(
  docker compose -f docker-compose.prod.yml exec -T db sh -ec \
    'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atqc "SELECT to_regclass('\''public.django_migrations'\'') IS NOT NULL"'
)"

if [ "$table_count" -le 0 ] || [ "$has_migrations" != "t" ]; then
  echo "Local PostgreSQL validation failed: public tables or django_migrations are missing." >&2
  exit 1
fi

migration_count="$(
  docker compose -f docker-compose.prod.yml exec -T db sh -ec \
    'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atqc "SELECT count(*) FROM django_migrations"'
)"

if [ "$migration_count" -le 0 ]; then
  echo "Local PostgreSQL validation failed: django_migrations is empty." >&2
  exit 1
fi

echo "Local PostgreSQL is valid: $table_count public tables, $migration_count migrations."
