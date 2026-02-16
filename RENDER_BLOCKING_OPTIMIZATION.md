# Оптимизация блокирующих отрисовку ресурсов

## Реализованные изменения

### 1. **Критический CSS (Inline)**
- Создан файл `templates/includes/_critical_css.html`
- Содержит минимальный CSS для hero-секции (above-the-fold)
- Инлайн-стили загружаются мгновенно без блокировки

### 2. **Асинхронная загрузка основного CSS**
- Используется техника `<link rel="preload" as="style" onload="...">`
- CSS загружается с высоким приоритетом, но не блокирует отрисовку
- Fallback через `<noscript>` для браузеров без JS

### 3. **Preload для критических шрифтов**
- Добавлен preload для `Lato-Regular.ttf` и `Lato-Bold.ttf`
- Браузер загружает шрифты раньше, избегая FOUT (Flash of Unstyled Text)

### 4. **Preconnect для внешних ресурсов**
- `dns-prefetch` и `preconnect` для `pinlite.dev`
- Ускоряет загрузку изображений с внешнего CDN

### 5. **Полифил для старых браузеров**
- Добавлен loadCSS polyfill в `base.html`
- Поддержка async CSS loading в старых браузерах

## Ожидаемые результаты

### До оптимизации:
- **Блокирующие ресурсы:** `app.css` (10 KiB, 150 мс)
- **Экономия:** ~1470 мс на LCP

### После оптимизации:
- **Критический CSS:** ~2 KiB inline (0 мс блокировки)
- **Основной CSS:** Загружается асинхронно
- **LCP улучшение:** ~1.5 секунды

## Структура загрузки

```
1. HTML парсится
2. Критический CSS применяется мгновенно (inline)
3. Hero-секция отрисовывается без задержки
4. app.css загружается параллельно (не блокирует)
5. Шрифты preload'ятся заранее
6. Полная страница стилизуется после загрузки app.css
```

## Проверка в PageSpeed Insights

После деплоя проверьте:
1. https://pagespeed.web.dev/
2. Введите `https://lily-salon.de`
3. Проверьте метрику "Устранение ресурсов, блокирующих отрисовку"
4. LCP должен улучшиться на ~1.5 сек

## Дополнительные рекомендации

### A. Минификация CSS (если еще не сделано)
```bash
# Использовать cssnano или аналог
npm install cssnano postcss-cli
postcss app.css --use cssnano -o app.min.css
```

### B. Сжатие Gzip/Brotli на сервере
```nginx
# nginx config
gzip on;
gzip_types text/css;
brotli on;
brotli_types text/css;
```

### C. HTTP/2 Push (опционально)
```python
# Django middleware или nginx
Link: </static/css/app.css>; rel=preload; as=style
```

### D. Service Worker для кэширования
```javascript
// Кэширование app.css для повторных визитов
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('v1').then((cache) => {
      return cache.addAll(['/static/css/app.css']);
    })
  );
});
```

## Метрики производительности

### Целевые показатели:
- **LCP:** < 2.5 сек (Good)
- **FCP:** < 1.8 сек (Good)
- **TTI:** < 3.8 сек (Good)

### Мониторинг:
```bash
# Lighthouse CI
npm install -g @lhci/cli
lhci autorun --collect.url=https://lily-salon.de
```

## Rollback (если нужно)

Если возникнут проблемы:

```bash
# Откатить изменения
git checkout HEAD~1 -- src/backend_django/templates/includes/_meta.html
git checkout HEAD~1 -- src/backend_django/templates/base.html
rm src/backend_django/templates/includes/_critical_css.html
```

## Файлы изменены:
- ✅ `templates/includes/_meta.html` - Асинхронная загрузка CSS
- ✅ `templates/base.html` - Полифил loadCSS
- ✅ `templates/includes/_critical_css.html` - Критический CSS (новый)

## Совместимость:
- ✅ Chrome/Edge 90+
- ✅ Firefox 85+
- ✅ Safari 14+
- ✅ Старые браузеры (через полифил)
