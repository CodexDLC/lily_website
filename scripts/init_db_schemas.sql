-- ═══════════════════════════════════════════
-- Initialize PostgreSQL schemas for multi-backend isolation.
--
-- Run this ONCE on a new database before running migrations.
-- Each backend uses its own schema to avoid table name conflicts.
-- This is especially useful with shared DBs like Neon.
--
-- Usage:
--   psql $DATABASE_URL -f scripts/init_db_schemas.sql
--   # or via Docker:
--   docker compose exec postgres psql -U postgres -d mydb -f /scripts/init_db_schemas.sql
-- ═══════════════════════════════════════════

-- Schema for FastAPI backend (SQLAlchemy + Alembic)
CREATE SCHEMA IF NOT EXISTS fastapi_app;

-- Schema for Django backend (Django ORM + migrations)
CREATE SCHEMA IF NOT EXISTS django_app;

-- Schema for Telegram Bot (if standalone with own DB models)
CREATE SCHEMA IF NOT EXISTS bot_app;

-- Grant usage to default user (adjust username if needed)
-- GRANT USAGE ON SCHEMA fastapi_app TO myuser;
-- GRANT USAGE ON SCHEMA django_app TO myuser;
-- GRANT USAGE ON SCHEMA bot_app TO myuser;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA fastapi_app TO myuser;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA django_app TO myuser;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA bot_app TO myuser;

-- Verify
SELECT schema_name FROM information_schema.schemata
WHERE schema_name IN ('fastapi_app', 'django_app', 'bot_app');
