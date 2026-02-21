# Контент в БД: Модель StaticTranslation

Мы решили вынести маркетинговые тексты из `.po` файлов в базу данных.

## Архитектура модели
```python
class StaticTranslation(models.Model):
    key = models.CharField(
        max_length=100,
        unique=True,
        help_text="Уникальный ключ для шаблона (например, 'home_hero_title')"
    )
    text = models.TextField(
        help_text="Текст для перевода"
    )
    # Поле 'text' будет расширено через django-modeltranslation:
    # text_de, text_en, text_ru, text_uk
```

## Как использовать в шаблоне
Вместо `{% trans "..." %}` используем переменную из контекста:
`{{ content.home_hero_title }}`

## Список текстов для миграции в БД

### Главная страница
- `home_hero_uptitle`: "Premium Beauty Salon"
- `home_hero_title`: "Die Kunst Ihrer Schönheit"
- `home_hero_description`: "Deutsche Qualitätsstandards treffen auf ukrainische Servicekunst..."
- `home_services_title`: "Unsere Leistungen"
- `home_services_subtitle`: "Wählen Sie eine Richtung"

### Страница команды
- `team_title`: "Unser Team"
- `team_subtitle`: "Profis, die Ihre Schönheit lieben"

### Страница контактов
- `contacts_title`: "Kontaktieren Sie uns"
- `contacts_description`: "Wir sind immer bereit, Ihre Fragen за beantworten"

## Преимущества
1. **Чистые .po файлы:** В них остается только UI (кнопки, меню).
2. **Управление из админки:** Маркетолог может менять тексты без участия программиста.
3. **SEO:** Легко управлять ключевыми словами в текстах для разных языков.
