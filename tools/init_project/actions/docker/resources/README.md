# Docker Action — Resources

Здесь будут шаблоны для генерации Docker-файлов.

## Планируемые ресурсы

```
resources/
├── Dockerfile.fastapi.tpl      # Dockerfile для FastAPI сервиса
├── Dockerfile.django.tpl       # Dockerfile для Django сервиса
├── Dockerfile.bot.tpl          # Dockerfile для Telegram Bot
├── Dockerfile.worker.tpl       # Dockerfile для ARQ Worker
├── Dockerfile.nginx.tpl        # Dockerfile для Nginx
├── docker-compose.dev.tpl      # docker-compose для dev окружения
├── docker-compose.prod.tpl     # docker-compose для production
├── nginx.conf.tpl              # Nginx конфиг (проксирование на backend)
└── ...
```

## Логика генерации

Docker Action читает шаблоны из этой папки и генерирует финальные файлы
в `deploy/` на основе выбора пользователя:

- Если выбран FastAPI → `Dockerfile.fastapi.tpl` → `deploy/fastapi/Dockerfile`
- Если включен бот → добавляет bot сервис в compose
- Если включен ARQ → добавляет worker контейнер
- Redis включается если есть бот или кэш
- Nginx включается если есть бэкенд
