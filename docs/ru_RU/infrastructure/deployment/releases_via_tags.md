# 🏷️ Релизы через Git Tags (Инструкция для разработчика)

[⬅️ Назад](./README.md) | [🏠 Главная документация](../../README.md)

---

## 📋 Обзор

Эта инструкция описывает **новый workflow** для выпуска релизов в продакшн. Вместо мёрджа в отдельную ветку `release`, мы используем **git tags** для триггера деплоя.

### Что изменилось?

**Старый способ (через ветку release):**
```bash
develop → main → release (PR) → деплой → обратный мёрдж в main/develop 😖
```

**Новый способ (через tags):**
```bash
develop → main (PR) → создать тег v1.2.3 → автоматический деплой 🚀
```

### Преимущества:

✅ **Нет обратного мёрджа** - больше не нужно мёрджить `release` обратно в `main` и `develop`
✅ **Чистая история** - теги чётко показывают какие версии были выпущены
✅ **Простой откат** - можно легко вернуться на любую версию: `git checkout v1.2.2`
✅ **Меньше веток** - только `develop` и `main`, без `release`

---

## 🚀 Пошаговая инструкция: Как сделать релиз

### Шаг 1: Проверка develop ветки

Убедитесь что все фичи которые вы хотите выпустить уже в `develop`:

```bash
git checkout develop
git pull origin develop
git log --oneline -10  # Посмотреть последние 10 коммитов
```

### Шаг 2: Запуск локальных проверок

Перед мёрджем в `main` **обязательно** проверьте код локально:

```bash
python tools/dev/check.py
```

Должно пройти:
- ✅ Ruff format (форматирование)
- ✅ Ruff lint (линтер)
- ✅ Mypy (проверка типов)
- ✅ Pytest unit tests

### Шаг 3: Мёрдж develop → main

Откройте Pull Request из `develop` в `main` на GitHub:

```bash
# На GitHub:
# 1. Идём в раздел "Pull requests"
# 2. Нажимаем "New pull request"
# 3. base: main ← compare: develop
# 4. Заполняем описание PR
# 5. Нажимаем "Create pull request"
```

**GitHub Actions автоматически запустит:**
- 🧪 Полный набор тестов (включая интеграционные)
- 🐳 Проверку сборки Docker образов

**Только после успешного прохождения CI** - мёржим PR!

### Шаг 4: Создание тега (Release Tag)

После того как PR смёржен в `main`, создаём тег:

```bash
# 1. Переключаемся на main и подтягиваем последние изменения
git checkout main
git pull origin main

# 2. Создаём тег с аннотацией (версия в формате v1.2.3)
git tag -a v1.2.3 -m "Release 1.2.3: Production fixes for booking flow"

# 3. Пушим тег на GitHub
git push origin v1.2.3
```

**Формат версии:** `vMAJOR.MINOR.PATCH` (например `v1.2.3`)

- **MAJOR** (1.x.x) - Несовместимые изменения API
- **MINOR** (x.2.x) - Новая функциональность (обратно совместимая)
- **PATCH** (x.x.3) - Исправления багов

### Шаг 5: Автоматический деплой

Как только вы пушите тег, **GitHub Actions автоматически**:

1. ✅ Проверяет доступность production сервера (SSH тест)
2. 🐳 Собирает Docker образы для всех сервисов:
   - Backend (Django)
   - Telegram Bot
   - Worker (ARQ tasks)
   - Nginx
3. 📦 Тегирует образы тремя тегами:
   - `latest` (последняя версия)
   - `v1.2.3` (версия релиза)
   - `sha-abc123` (git commit hash)
4. 🚢 Пушит образы в GitHub Container Registry (GHCR)
5. 📋 Копирует конфиги на VPS (`/opt/lily_website/deploy/`)
6. 🔄 Запускает миграции Django (`python manage.py migrate`)
7. 📦 Собирает статику (`collectstatic`)
8. 🚀 Перезапускает все контейнеры на production сервере

### Шаг 6: Проверка деплоя

После деплоя проверьте что всё работает:

```bash
# Смотрим статус workflow на GitHub:
# https://github.com/CodexDLC/lily_website/actions

# Или проверяем напрямую на сервере (если есть SSH доступ):
ssh user@46.225.138.167

# Проверка контейнеров:
docker ps

# Логи backend:
docker logs lily_website-backend --tail 50

# Логи bot:
docker logs lily_website-telegram_bot --tail 50
```

**Проверка через браузер:**
- Открыть: https://lily-salon.de/
- Открыть админку: https://lily-salon.de/admin/
- Проверить что новые изменения видны на сайте

---

## 🛠️ Дополнительные сценарии

### Сценарий 1: Hotfix (срочное исправление в production)

Если нужно срочно исправить баг в продакшне:

```bash
# 1. Создаём hotfix ветку от main
git checkout main
git pull origin main
git checkout -b hotfix/critical-booking-error

# 2. Исправляем баг
# ... редактируем код ...

# 3. Коммитим
git add .
git commit -m "fix(booking): critical error in payment validation"

# 4. Открываем PR напрямую в main
git push origin hotfix/critical-booking-error

# 5. После мёрджа в main - создаём тег:
git checkout main
git pull origin main
git tag -a v1.2.4 -m "Hotfix 1.2.4: Critical booking error"
git push origin v1.2.4

# 6. Бэкпортим в develop (cherry-pick):
git checkout develop
git cherry-pick <commit-hash>  # Хэш коммита из main
git push origin develop
```

### Сценарий 2: Откат на предыдущую версию

Если после релиза что-то сломалось:

```bash
# 1. Смотрим список тегов:
git tag -l

# Вывод:
# v1.0.0
# v1.1.0
# v1.2.0
# v1.2.1
# v1.2.2
# v1.2.3  ← текущая (сломанная)

# 2. Откатываемся на предыдущий стабильный тег:
git checkout main
git reset --hard v1.2.2

# 3. Создаём новый тег для отката:
git tag -a v1.2.4 -m "Rollback to v1.2.2 due to critical bug"
git push origin v1.2.4 --force

# GitHub Actions автоматически задеплоит v1.2.4
```

### Сценарий 3: Просмотр изменений между версиями

Чтобы понять что изменилось между двумя релизами:

```bash
# Сравнение двух тегов:
git log v1.2.0..v1.2.3 --oneline

# Или полный diff:
git diff v1.2.0 v1.2.3

# Список файлов которые изменились:
git diff --name-only v1.2.0 v1.2.3
```

---

## 📝 Naming Convention для тегов

### Правильные примеры:

✅ `v1.0.0` - Первый мажорный релиз
✅ `v1.2.3` - Обычный релиз
✅ `v2.0.0` - Мажорное обновление с breaking changes
✅ `v1.2.4-hotfix` - Hotfix релиз (опционально добавить суффикс)

### Неправильные примеры:

❌ `1.2.3` - Нет префикса `v`
❌ `release-1.2.3` - Неправильный формат
❌ `v1.2` - Отсутствует PATCH номер

**Важно:** GitHub Actions триггерится только на теги начинающиеся с `v*`

---

## 🔍 Troubleshooting (Решение проблем)

### Проблема 1: Деплой не запустился после пуша тега

**Причина:** GitHub Actions не видит workflow триггер.

**Решение:**
```bash
# Проверьте что тег начинается с 'v':
git tag -l

# Удалите неправильный тег:
git tag -d wrong-tag
git push origin :refs/tags/wrong-tag

# Создайте правильный тег:
git tag -a v1.2.3 -m "Release 1.2.3"
git push origin v1.2.3
```

### Проблема 2: GitHub Actions упал на этапе миграций

**Причина:** Django миграции не применились на production.

**Решение:**
```bash
# SSH на сервер:
ssh user@46.225.138.167

cd /opt/lily_website/deploy

# Проверить логи backend:
docker logs lily_website-backend --tail 100

# Применить миграции вручную:
docker compose -f docker-compose.prod.yml run --rm backend python manage.py migrate

# Перезапустить контейнеры:
docker compose -f docker-compose.prod.yml restart backend
```

### Проблема 3: Не могу создать тег (rejected)

**Причина:** Тег с таким именем уже существует.

**Решение:**
```bash
# Удалить локальный тег:
git tag -d v1.2.3

# Удалить тег на удалённом репозитории:
git push origin :refs/tags/v1.2.3

# Создать новый тег:
git tag -a v1.2.4 -m "Release 1.2.4"
git push origin v1.2.4
```

---

## 🔐 Безопасность и секреты

Для деплоя используются следующие **GitHub Secrets**:

| Secret | Описание |
|:---|:---|
| `HOST` | IP-адрес production сервера (46.225.138.167) |
| `USERNAME` | SSH пользователь на сервере |
| `SSH_KEY` | Приватный SSH ключ для подключения |
| `ENV_FILE` | Содержимое `.env.production` файла |
| `DOMAIN_NAME` | Доменное имя (lily-salon.de) |
| `REDIS_PASSWORD` | Пароль для Redis |

**Важно:** Секреты хранятся только в GitHub. Никогда не коммитьте `.env.production` в git!

---

## 📚 Связанные документы

- **[Английская версия (полная)](../../en_EN/infrastructure/deployment/releases_via_tags.md)** - Детальная техническая документация
- **[Git Flow Analysis](../../en_EN/infrastructure/git_flow_analysis.md)** - Анализ workflow стратегий
- **[Git Flow & Branching Strategy](../../en_EN/infrastructure/git_flow.md)** - Текущая стратегия веток

---

## 🎯 Чеклист перед релизом

Перед каждым релизом проверьте:

- [ ] Все фичи протестированы локально
- [ ] Запущен `check_local.ps1` и все проверки прошли
- [ ] PR из `develop` в `main` создан и CI прошёл
- [ ] PR смёржен в `main`
- [ ] Тег создан в правильном формате (`v*.*.*`)
- [ ] Тег запушен на GitHub: `git push origin v1.2.3`
- [ ] GitHub Actions workflow запустился и прошёл успешно
- [ ] Production сайт проверен: https://lily-salon.de/
- [ ] Логи backend/bot проверены на отсутствие ошибок
- [ ] Контейнеры работают стабильно (не перезагружаются)

---

**Последнее обновление:** 2026-02-16
**Автор:** CodexDLC
**Статус:** Активная инструкция (используется для production релизов)
