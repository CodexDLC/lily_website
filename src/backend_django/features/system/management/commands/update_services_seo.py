import json

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand
from features.main.models import Service


class Command(BaseCommand):
    help = "Update SEO fields for Services from initial_seo.json"

    def handle(self, *args, **options):
        # Читаем конкретный файл для услуг
        file_path = settings.BASE_DIR / "features" / "system" / "fixtures" / "seo" / "initial_seo.json"

        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        try:
            with open(file_path, encoding="utf-8") as f:
                all_seo_data = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading JSON: {e}"))
            return

        slugs = list(all_seo_data.keys())
        services = Service.objects.filter(slug__in=slugs)
        services_map = {s.slug: s for s in services}

        updated_count = 0
        skipped_count = 0

        for slug, new_data in all_seo_data.items():
            service = services_map.get(slug)
            if not service:
                continue

            has_changes = False
            for field, new_value in new_data.items():
                try:
                    current_value = getattr(service, field, None)
                    if current_value != new_value:
                        setattr(service, field, new_value)
                        has_changes = True
                except Exception:
                    continue

            if has_changes:
                service.save()
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"  [UPDATE] Service SEO: {slug}"))
                # Invalidate cache
                cache.delete_many([f"service_detail_{service.slug}", f"category_detail_{service.category.slug}"])
            else:
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(f"\nFinished: {updated_count} updated, {skipped_count} skipped."))
