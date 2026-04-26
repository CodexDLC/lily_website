# План рефакторинга Django Admin (Lily Website)

Этот документ содержит подробный план модернизации административной панели проекта. Основная цель — превратить стандартный интерфейс в профессиональный инструмент управления бизнесом с использованием темы `django-unfold`.

---

## Общие принципы

1.  **Декораторы**: Везде используем `@admin.register(Model)`.
2.  **Unfold**: Все классы наследуются от `unfold.admin.ModelAdmin`.
3.  **Производительность**: Обязательное использование `autocomplete_fields` для ForeignKey и ManyToMany связей (требует наличия `search_fields` в связанных моделях).
4.  **Визуализация**: Статусы отображаются в виде цветных бейджей через `admin.display` и `mark_safe`.
5.  **Организация**: Поля группируются в `fieldsets` с логичными заголовками и иконками.

---

## 1. Бронирования (features/booking)

### Файл: `src/lily_backend/features/booking/admin.py`

#### MasterAdmin (Мастера)
- **list_display**: `name`, `status_badge`, `is_owner`, `is_public`, `order`, `telegram_username`.
- **list_editable**: `order`, `is_public`, `is_owner`, `status`.
- **list_filter**: `status`, `is_public`, `is_owner`, `categories`.
- **autocomplete_fields**: `categories`, `user`.
- **fieldsets**:
    - "Основная информация" (имя, фото, описание).
    - "Статус и видимость" (status, is_public, order).
    - "Рабочее время" (start, end, breaks).
    - "Ограничения бронирования" (buffer, advance days).
    - "Профессиональные данные" (категории, опыт).

#### AppointmentAdmin (Записи)
- **list_display**: `client_link`, `master_badge`, `service_badge`, `datetime_start`, `status_badge`, `price_badge`.
- **list_filter**: `status`, `master`, `service`, `datetime_start`.
- **autocomplete_fields**: `client`, `master`, `service`.
- **fieldsets**:
    - "Клиент и Услуга" (client, service, master).
    - "Расписание" (datetime_start, datetime_end).
    - "Финансы" (price, currency, status).
    - "Метаданные" (created_at, updated_at).

#### AppointmentGroupAdmin (Групповые записи/Корзина)
- **list_display**: `id`, `client`, `status_badge`, `source`, `combo`, `created_at`.
- **autocomplete_fields**: `client`, `combo`.

---

## 2. Основной каталог (features/main)

### Файл: `src/lily_backend/features/main/admin/catalog.py`

#### ServiceAdmin (Услуги)
- **list_display**: `name`, `category_badge`, `price_tag`, `duration_tag`, `is_active`, `is_addon`, `order`.
- **list_editable**: `price`, `duration`, `order`, `is_active`.
- **autocomplete_fields**: `category`, `masters`, `excludes`.
- **fieldsets**:
    - "Базовая информация" (name, slug, category, image).
    - "Ценообразование и Длительность" (price, duration, info fields).
    - "Настройки SEO" (из SeoMixin).
    - "Системные настройки" (masters, excludes, order).

#### ServiceCategoryAdmin (Категории)
- **list_display**: `name`, `bento_group`, `is_active`, `order`.
- **list_editable**: `order`, `bento_group`, `is_active`.

---

## 3. Коммуникации (features/conversations)

### Файл: `src/lily_backend/features/conversations/admin.py`

#### MessageAdmin (Сообщения)
- **list_display**: `sender_info`, `topic_badge`, `status_badge`, `source_badge`, `channel_badge`, `created_at`.
- **list_editable**: `status`, `topic`.
- **list_filter**: `status`, `topic`, `source`, `channel`, `is_read`, `is_archived`.
- **fieldsets**:
    - "Отправитель" (name, email, phone).
    - "Контент" (subject, body).
    - "Классификация" (topic, status, source, channel).
    - "Управление" (is_read, is_archived, admin_notes).

#### CampaignAdmin (Рассылки)
- **list_display**: `subject`, `status_badge`, `locale`, `created_at`, `sent_at`.
- **fieldsets**:
    - "Параметры рассылки" (subject, body, template_key, is_marketing).
    - "Аудитория" (audience_filter, locale).
    - "Статус выполнения" (status, sent_at, status_reason).

---

## 4. Системные настройки и Клиенты (system)

### Файл: `src/lily_backend/system/admin/client.py`

#### ClientAdmin (Клиенты)
- **list_display**: `full_name`, `phone`, `email`, `status_badge`, `is_ghost`, `created_at`.
- **list_editable**: `status`.
- **autocomplete_fields**: `user`.
- **fieldsets**:
    - "Личные данные" (first_name, last_name, patronymic, user).
    - "Контакты" (email, phone).
    - "Согласия" (marketing, analytics).
    - "Системный статус" (status, is_ghost, access_token).

### Файл: `src/lily_backend/system/admin/settings.py`

#### SiteSettingsAdmin (Настройки сайта)
- **list_display**: `company_name`, `phone`, `email`, `social_status_badge`.
- **fieldsets**:
    - "Общая информация" (name, owner, logo).
    - "Контакты и Адрес" (phone, email, street, zip).
    - "Рабочие часы" (weekdays, sat, sun).
    - "Маркетинг и Аналитика" (GA, GTM, FB Pixel).
    - "Технические параметры" (maintenance_mode, scripts).

---

## 5. Уведомления (features/notifications)

### Файл: `src/lily_backend/features/notifications/admin.py`

#### NotificationLogAdmin (Логи уведомлений) [NEW]
- **list_display**: `event_type`, `recipient`, `channel_badge`, `status_badge`, `sent_at`.
- **list_filter**: `status`, `channel`, `event_type`.
- **readonly_fields**: `sent_at`, `error_message`, `context_preview`.

---

## 6. Профили и Лояльность (system)

### Файл: `src/lily_backend/system/admin/loyalty.py`
- **list_display**: `profile`, `level_badge`, `progress_percent`, `calculated_at`.

### Файл: `src/lily_backend/system/admin/user_profile.py`
- **list_display**: `user`, `get_full_name`, `phone`, `source`, `created_at`.
- **autocomplete_fields**: `user`.
