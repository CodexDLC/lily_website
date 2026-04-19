# Django 6 Upgrade Plan

## Контекст

Цель: подготовить `lily_website` к переходу на `Django 6.0.4+`.

Это не файл про один tracking-рефакторинг. Это рабочая точка входа по всем blocker'ам апгрейда.

Текущее состояние:

- проект зафиксирован на `django>=5.2.13,<6.0`
- `uv.lock` собран под `Django 5.2.13`
- основной upgrade ещё не начат
- сначала снимаем ключевые blocker'ы, потом делаем upgrade-ветку и пробуем реальный запуск

---

## Главные blocker-зоны

### 1. Tracking и legacy `django-redis`

Статус: `TODO`

Что уже известно:

- библиотечный `codex_django.tracking` уже переведён на прямой `redis.Redis.from_url(...)`
- локальный Lily tracking всё ещё держит legacy-менеджер на `django_redis.get_redis_connection(...)`

Текущие project-level точки:

- [src/lily_backend/tracking/manager.py](C:/install/projects/clients/lily_website/src/lily_backend/tracking/manager.py)
- [src/lily_backend/tracking/selector.py](C:/install/projects/clients/lily_website/src/lily_backend/tracking/selector.py)
- [src/lily_backend/tracking/recorder.py](C:/install/projects/clients/lily_website/src/lily_backend/tracking/recorder.py)
- [src/lily_backend/tracking/flush.py](C:/install/projects/clients/lily_website/src/lily_backend/tracking/flush.py)

Что хотим поменять:

- убрать project-local tracking Redis слой
- переключить tracking на библиотечный `codex_django.tracking`
- убрать зависимость tracking от `django-redis`

Критерий завершения:

- в tracking-коде проекта больше нет `django_redis`
- tracking использует библиотечный Redis runtime
- cabinet analytics / flush / recorder продолжают работать

---

### 2. Django cache/session backend

Статус: `TODO`

Текущая живая точка:

- [src/lily_backend/core/settings/modules/cache.py](C:/install/projects/clients/lily_website/src/lily_backend/core/settings/modules/cache.py)

Что сейчас там:

- `django_redis.cache.RedisCache`
- `django_redis.client.DefaultClient`
- cache/session слой завязан на `django-redis`

Что надо оценить:

- остаёмся ли временно на `django-redis` только ради cache/session
- или переводим cache/session на наш Redis/runtime слой тоже
- насколько это обязательно до перехода на Django 6, а насколько можно вынести в следующий этап

Ключевой вопрос:

- нужен ли `django-redis` проекту после переноса tracking, или он останется только ради Django cache backend

---

### 3. Admin stack

Статус: `TODO`

Что надо оценить:

- `unfold`
- `modeltranslation`
- кастомные `ModelAdmin`
- monkey-patch / admin wiring

Почему это blocker:

- если `unfold` плохо переживает Django 6, можно отказаться от него без ущерба для клиентского кабинета
- это отдельная зона риска, не связанная с основным user-facing runtime

Что хотим понять:

- есть ли смысл чинить `unfold`
- или проще снять его / упростить admin-слой для совместимости с Django 6

---

### 4. Устаревшие / изменённые Django API в нашем коде и `codex-django`

Статус: `TODO`

Это уже не про “внешнюю библиотеку”, а про наш собственный код.

Что надо проверить:

- старые imports
- deprecated API
- admin hooks
- sitemap / i18n / template tags
- middleware / request-response hooks
- management commands
- любые места, где Django 6 мог поменять контракт

Главный смысл этой проверки:

- найти реальные кодовые места, которые могут отвалиться при runtime upgrade
- не тратить время на абстрактную “совместимость codex-django”, если это наш код и мы его всё равно можем править

---

### 5. Packaging / lock / dependency resolution

Статус: `TODO`

Текущие точки:

- [pyproject.toml](C:/install/projects/clients/lily_website/pyproject.toml)
- [uv.lock](C:/install/projects/clients/lily_website/uv.lock)

Что надо сделать позже:

- снять cap `<6.0`
- выставить целевую версию `Django 6.0.4+`
- пересобрать lock-файл

Важно:

- это делается после первичной оценки blocker'ов
- не имеет смысла первым шагом, пока не понятны tracking/cache/admin риски

---

## Что делаем прямо сейчас

Первый подтверждённый блок работ:

1. Перенос tracking на библиотечный runtime.

После него:

2. Повторно посмотреть, где ещё реально нужен `django-redis`.
3. Оценить cache/session слой.
4. Оценить admin stack (`unfold` и смежное).
5. Пройтись по коду на предмет старых Django API.
6. Только потом делать пробный upgrade на Django 6.

---

## Не учитывать как blocker

Следующие точки сейчас не считаем живыми blocker'ами:

- `archive/**`
- старые docs про `django_redis`
- общие рассуждения про “совместимость codex-django”, если речь идёт о нашем коде, который мы можем менять сами

---

## Рабочий порядок

### Этап A. Снять первый blocker

- tracking -> библиотечный runtime

### Этап B. Дооценка остальных blocker'ов

- cache/session backend
- admin stack
- legacy Django API usages

### Этап C. Боевой preflight

- bump Django
- rebuild lock
- `manage.py check`
- tests
- smoke runtime

---

## Итоговая цель

Подойти к переходу на Django 6 не “теорией”, а с коротким списком реальных задач:

- tracking переведён
- `django-redis` usage локализован
- admin-risk понятен
- старые Django API найдены или исключены
- после этого можно безопасно пробовать реальный upgrade
