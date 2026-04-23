# Redis feature flag runbook

## Flag

`USE_CODEX_REDIS_BACKENDS` controls the Django cache and session Redis backend in production.

- `False`: use `django_redis.cache.RedisCache` and DB-backed Django sessions.
- `True`: use `codex_django.cache.backends.redis.RedisCache` and `codex_django.sessions.backends.redis`.

Keep `django-redis` installed until the codex backend has run successfully in production for at least two weeks.

## Staging rollout

1. Deploy the build with `codex-django==0.6.0` and `codex-platform>=0.4.0`.
2. Set `USE_CODEX_REDIS_BACKENDS=True` in staging.
3. Run:

   ```sh
   docker compose -f deploy/docker-compose.prod.yml run --rm -T backend python manage.py update_site_settings --force
   docker compose -f deploy/docker-compose.prod.yml run --rm -T backend python manage.py update_site_settings --force
   docker compose -f deploy/docker-compose.prod.yml run --rm -T backend python manage.py update_all_content
   docker compose -f deploy/docker-compose.prod.yml run --rm -T backend python manage.py load_catalog
   ```

4. Check admin login, `/ru/cabinet/` twice, `/ru/team/`, and `/ru/contacts/`.

## Monitoring

Watch backend logs for:

- `AttributeError` around Redis managers or `_client`.
- `Event loop is closed`.
- `Future attached to a different loop`.
- `redis.exceptions.DataError`.
- Redis authentication failures.

Also compare `/ru/cabinet/` p95 latency against the fallback backend. A regression above 50ms needs a follow-up for connection pooling.

## Production rollout and rollback

Enable `USE_CODEX_REDIS_BACKENDS=True` after staging has been clean for one working day.

Rollback is changing `USE_CODEX_REDIS_BACKENDS=False` and restarting the backend. No code rollback is required.

## Redis password escaping

Compose files must reference Redis secrets as shell variables inside the container, for example `$${REDIS_PASSWORD}`. A literal `$` in `.env` passwords must not be interpolated by Docker Compose.
