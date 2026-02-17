import json

from django.conf import settings
from django.core.management.base import BaseCommand
from features.system.models.seo import StaticPageSeo


class Command(BaseCommand):
    help = "Update SEO fields for Static Pages from static_pages_seo.json"

    def handle(self, *args, **options):
        # Читаем конкретный файл для статических страниц
        file_path = settings.BASE_DIR / "features" / "system" / "fixtures" / "seo" / "static_pages_seo.json"

        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        try:
            with open(file_path, encoding="utf-8") as f:
                all_seo_data = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading JSON: {e}"))
            return

        updated_count = 0
        skipped_count = 0

        for page_key, new_data in all_seo_data.items():
            # Получаем или создаем объект SEO для страницы
            seo_obj, created = StaticPageSeo.objects.get_or_create(page_key=page_key)

            has_changes = False
            for field, new_value in new_data.items():
                try:
                    current_value = getattr(seo_obj, field, None)
                    if current_value != new_value:
                        setattr(seo_obj, field, new_value)
                        has_changes = True
                except Exception:
                    continue

            if has_changes:
                seo_obj.save()
                updated_count += 1
                status = "CREATED" if created else "UPDATE"
                self.stdout.write(self.style.SUCCESS(f"  [{status}] Static SEO: {page_key}"))
            else:
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(f"\nFinished: {updated_count} updated, {skipped_count} skipped."))
