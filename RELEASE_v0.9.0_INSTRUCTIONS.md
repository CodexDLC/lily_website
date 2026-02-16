# 🚀 Инструкция по релизу v0.9.0

## Шаг 1: Создать PR develop → main на GitHub

Зайдите на GitHub и создайте Pull Request:

**URL:** https://github.com/CodexDLC/lily_website/compare/main...develop

**Заголовок PR:**
```
Release v0.9.0: Tag-based deployment migration and bug fixes
```

**Описание PR:**
```markdown
## 📋 Summary

This release includes the migration to tag-based deployment workflow and several important bug fixes.

### 🚀 Major Changes

- **Tag-based releases**: Migrated from `release` branch to git tag workflow
  - New workflow: `deploy-production-tag.yml`
  - Removed: `cd-release.yml`, `check-release-source.yml`
  - Comprehensive documentation added (EN/RU)

- **Bot configuration fix**: Added JSON validator for `telegram_topics` field
  - Fixes bot restart loop on production

- **Booking service**: Updated service visibility logic

### 📚 Documentation Updates

- Added complete tag-based release guides (EN/RU)
- Added migration guide from release branch
- Updated all workflow documentation
- Added PWA setup documentation
- Added bot_menu contracts and logic docs

### 🔧 Bug Fixes

- Fixed `telegram_topics` parsing error in bot config
- Updated service visibility logic in booking

## 🧪 Test Plan

- [x] Local checks passed (`check_local.ps1`)
- [x] CI develop passed
- [ ] CI main tests (will run on PR)
- [ ] Docker build verification (will run on PR)

## 📦 Deployment Plan

After merge:
1. Create tag: `git tag -a v0.9.0 -m "Release 0.9.0: Tag-based deployment migration"`
2. Push tag: `git push origin v0.9.0`
3. GitHub Actions will automatically deploy to production

## 🔗 Related Issues

- Fixes production bot restart loop
- Implements new deployment workflow

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

---

## Шаг 2: Дождаться прохождения CI

После создания PR, GitHub Actions запустит:
- ✅ CI Main workflow (полные тесты)
- ✅ Docker build verification

**Убедитесь что все проверки прошли успешно перед мёрджем!**

---

## Шаг 3: Смёржить PR

После успешного прохождения CI:
1. Нажать кнопку "Merge pull request"
2. Подтвердить мёрдж

---

## Шаг 4: Создать и запушить тег v0.9.0

После мёрджа PR, выполните следующие команды:

```bash
# 1. Переключиться на main и подтянуть изменения
git checkout main
git pull origin main

# 2. Создать аннотированный тег v0.9.0
git tag -a v0.9.0 -m "Release 0.9.0: Tag-based deployment migration and bug fixes

Major changes:
- Migrated to tag-based deployment workflow
- Fixed telegram_topics parsing error in bot
- Updated service visibility logic
- Comprehensive documentation updates

This is the first release using the new tag-based deployment system."

# 3. Запушить тег на GitHub
git push origin v0.9.0
```

---

## Шаг 5: Мониторинг деплоя

После пуша тега:

1. **Открыть GitHub Actions:** https://github.com/CodexDLC/lily_website/actions
2. **Найти workflow:** "Deploy Production (Tag-based)" для тега `v0.9.0`
3. **Отслеживать прогресс:**
   - ✅ Check Server Availability
   - ✅ Build & Deploy to VPS

**Ожидаемое время:** ~5-10 минут

---

## Шаг 6: Верификация на production

После успешного деплоя:

### A. Проверка через браузер

1. **Главная страница:** https://lily-salon.de/
   - Должна загрузиться без ошибок

2. **Админка Django:** https://lily-salon.de/admin/
   - Проверить что открывается

3. **Booking flow:** https://lily-salon.de/booking/
   - Проверить что работает

### B. Проверка через SSH (если есть доступ)

```bash
# Подключиться к серверу
ssh user@46.225.138.167

# Проверить статус контейнеров
docker ps

# Проверить логи backend (не должно быть DisallowedHost ошибок)
docker logs lily_website-backend --tail 100 | grep -i error

# Проверить логи bot (не должно быть telegram_topics ошибок)
docker logs lily_website-telegram_bot --tail 100 | grep -i error

# Проверить что контейнеры НЕ перезагружаются
docker ps --format "table {{.Names}}\t{{.Status}}"
```

**Ожидаемый результат:**
- ✅ Все контейнеры в статусе "Up" (без постоянных рестартов)
- ✅ Нет ошибок `DisallowedHost` в логах backend
- ✅ Нет ошибок `error parsing value for field 'telegram_topics'` в логах bot

---

## Шаг 7: Проверка новых фич

### Telegram Bot Topics

1. Создать тестовую запись в категории "hair" через админку
2. Проверить что уведомление в Telegram попало в правильный topic (topic_id=2)

---

## 🎉 Поздравляю с первым tag-based релизом!

После успешного деплоя:

1. ✅ Workflow с release веткой больше не используется
2. ✅ Новый tag-based workflow работает
3. ✅ Production сервер стабилен
4. ✅ Все сервисы запущены без ошибок

---

## 🔄 Следующие релизы

Для следующих релизов повторяйте процесс:

```bash
# 1. Мёржим develop → main через PR
# 2. Создаём тег
git checkout main
git pull origin main
git tag -a v0.9.1 -m "Release 0.9.1: Description"
git push origin v0.9.1

# GitHub Actions автоматически задеплоит!
```

Полная инструкция: `docs/ru_RU/infrastructure/deployment/releases_via_tags.md`

---

## ⚠️ Rollback Plan (если что-то пойдёт не так)

Если после деплоя v0.9.0 что-то сломалось:

```bash
# 1. Откатиться на последний стабильный коммит в main
git checkout main
git log --oneline  # Найти последний стабильный коммит

# 2. Создать rollback тег
git tag -a v0.9.1 -m "Rollback: revert to stable version"
git push origin v0.9.1

# Или вручную на сервере:
ssh user@46.225.138.167
cd /opt/lily_website/deploy
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

---

**Дата создания:** 2026-02-16
**Статус:** Готов к выполнению
**Следующий шаг:** Создать PR на GitHub
