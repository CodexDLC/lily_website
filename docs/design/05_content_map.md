---
render_with_liquid: false
---

# 05. КОНТЕНТ-СТРАТЕГИЯ И ЛОКАЛИЗАЦИЯ (CONTENT MAP)

[📂 Design Index](./README.md) > 📄 Content Map

---

## 1. Мультиязычность (Internationalization / i18n)
Система проектируется на базе `Django Translation`. Поддерживаем 4 языка.
*   **Языки:**
    *   **DE (German):** Обязателен для юридических страниц (Impressum, AGB) и местной аудитории.
    *   **RU (Russian) / UA (Ukrainian):** Потенциально основные языки коммуникации (зависит от целевой аудитории).
    *   **EN (English):** Дополнительный.
*   **Техническая реализация:**
    *   Весь статический текст (меню, кнопки, заголовки) заворачивается в теги перевода `{% trans "Text" %}`.
    *   Динамический контент (описания услуг, био мастеров) хранится в базе данных с дублированием полей (напр. `description_de`, `description_ru`).

## 2. Правило "Чистых Медиа" (No Embedded Text)
*   **Принцип:** Текст никогда не "запекается" внутри картинок (JPG/PNG).
*   **Почему:** Чтобы текст можно было автоматически переводить при переключении языка, индексировать поисковиками и менять размер на мобильных.
*   **Реализация:**
    *   Логотип (фон хедера) — используется как подложка. Текст "Beauty Salon" и навигация верстаются поверх HTML-тегами.
    *   Карточки услуг/мастеров — фото чистое, подписи идут отдельным блоком `div` поверх или снизу.

## 3. Структура текстов (Copywriting)

### A. Хедер и Обложка (Hero)
*   **Слоган:** Короткий, эмоциональный.
    *   *Пример:* "Искусство вашей красоты" (RU) / "Die Kunst Ihrer Schönheit" (DE).
*   **CTA Кнопка:** Глагол действия. "Записаться" / "Termin buchen".

### B. Блок "Доверие" (Trust)
*   Текстовый заголовок над каруселью логотипов.
*   *Суть:* Пояснение, что это за логотипы (Школы, Партнеры, Используемая косметика).

### C. Футер (Legal)
*   **Важно:** В Германии разделы `Impressum` (Выходные данные) и `Datenschutz` (Приватность) должны быть доступны на немецком языке всегда, даже если сайт переключен на русский.

## 4. SEO (Поисковая оптимизация)
*   Тексты должны содержать гео-привязку (Köthen, Germany) в заголовках H1/H2 на всех языках.

---

## 5. ТЕХНИЧЕСКИЙ SEO & GEO (Паспорт сайта для ИИ)

Чтобы поисковики и нейросети (Gemini, ChatGPT, Siri) понимали, что мы находимся в Кётене и оказываем услуги, внедряем 3 уровня разметки.

### A. GEO Meta Tags (Гео-привязка)
Прописываются в `<head>`. Жестко привязывают сайт к координатам, чтобы мы ранжировались в "Google Maps" и локальной выдаче.
```html
<meta name="geo.region" content="DE-ST" />
<meta name="geo.placename" content="Köthen (Anhalt)" />
<meta name="geo.position" content="51.75;11.96" />
<meta name="ICBM" content="51.75, 11.96" />
```

### B. Open Graph (Для соцсетей)
Чтобы при отправке ссылки в WhatsApp/Telegram была красивая картинка-превью, а не пустой квадрат.

```html
<meta property="og:type" content="business.business">
<meta property="og:title" content="LILY Beauty Salon - Friseur in Köthen">
<meta property="og:url" content="https://lily-salon.de">
<meta property="og:image" content="https://lily-salon.de/static/img/social-share.jpg">
<meta property="business:contact_data:street_address" content="[Улица Салона]">
<meta property="business:contact_data:locality" content="Köthen">
<meta property="business:contact_data:country_name" content="Germany">
```

### C. JSON-LD Schema (Главное для ИИ)
Это скрытый код, который "скармливает" роботам структуру бизнеса. ИИ читает именно это. Используем схему `BeautySalon` (дочерняя от `LocalBusiness`).

**Что включаем в JSON:**
*   `@type`: "BeautySalon"
*   `name`: "LILY Beauty Salon"
*   `image`: Ссылка на лого/фасад.
*   `priceRange`: "€€" (Средний/Высокий).
*   `address`: Полный адрес с индексом.
*   `telephone`: Кликабельный номер.
*   `openingHours`: График работы (чтобы Siri знала, открыты ли мы сейчас).
*   `hasMap`: Ссылка на Google Maps CID.

### D. Hreflang (Для языков)
Чтобы Google не путал русскую и немецкую версии и не считал их дублями.

```html
<link rel="alternate" hreflang="de" href="https://site.de/" />
<link rel="alternate" hreflang="ru" href="https://site.de/ru/" />
<link rel="alternate" hreflang="uk" href="https://site.de/ua/" />
<link rel="alternate" hreflang="x-default" href="https://site.de/" />
```