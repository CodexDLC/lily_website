from jinja2 import Environment, FileSystemLoader

# Настраиваем Jinja2 на текущую папку
file_loader = FileSystemLoader(".")
env = Environment(loader=file_loader)

# Тестовые данные (имитация того, что пришлет воркер)
context = {
    "site_url": "https://lily-salon.de",
    "logo_url": "https://pinlite.dev/media/storage/a3/65/a365b5fedad7fb5779bc5fcf63f00ebc19ed90808c4010a0fbec7207773ca95e.png",
    "greeting": "Guten Tag Anna,",
    "name": "Anna",
    "service_name": "Maniküre Komplett",
    "date": "25.10.2023",
    "time": "14:30",
    "salon_address": "Berliner Str. 42, 10117 Berlin",
    # Динамические токены для ссылок
    "action_token": "uuid-for-booking-action",  # Тестовый токен для отмены/переноса
    # Для напоминания
    "intro_text": "Wir freuen uns auf Ihren Besuch morgen!",
    # Для отмены
    "cancellation_reason": "Krankheit des Mitarbeiters",
    # Для возвращения
    "body_text": "Es ist schon 3 Wochen her seit Ihrem letzten Besuch. Gönnen Sie sich eine Auszeit!",
}

templates = ["confirmation.html", "cancellation.html", "reminder.html", "reengagement.html"]

print("Generating previews...")
for template_name in templates:
    try:
        template = env.get_template(template_name)
        output = template.render(context)

        preview_filename = f"preview_{template_name}"
        with open(preview_filename, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"OK: {preview_filename}")
    except Exception as e:
        print(f"ERROR {template_name}: {e}")
