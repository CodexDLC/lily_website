import json

from core.logger import log
from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand
from features.main.models import Service


class Command(BaseCommand):
    help = "Update SEO fields for Services from initial_seo.json"

    def handle(self, *args, **options):
        log.info("Command: update_services_seo | Action: Start")

        # Read specific file for services
        file_path = settings.BASE_DIR / "features" / "system" / "fixtures" / "seo" / "initial_seo.json"
        log.debug(f"Command: update_services_seo | Action: LoadFixture | path={file_path}")

        if not file_path.exists():
            log.error(f"Command: update_services_seo | Action: Failed | error=File not found | path={file_path}")
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        try:
            with open(file_path, encoding="utf-8") as f:
                all_seo_data = json.load(f)
        except Exception as e:
            log.error(f"Command: update_services_seo | Action: Failed | error=JSONError | message={e}")
            self.stdout.write(self.style.ERROR(f"Error reading JSON: {e}"))
            return

        slugs = list(all_seo_data.keys())
        services = Service.objects.filter(slug__in=slugs)
        services_map = {s.slug: s for s in services}

        updated_count = 0
        skipped_count = 0

        log.debug(f"Command: update_services_seo | Action: ProcessingSlugs | count={len(slugs)}")

        for slug, new_data in all_seo_data.items():
            service = services_map.get(slug)
            if not service:
                log.warning(f"Command: update_services_seo | Action: SkipSlug | slug={slug} | reason=NotFoundInDB")
                continue

            has_changes = False
            changed_fields = []
            for field, new_value in new_data.items():
                try:
                    current_value = getattr(service, field, None)
                    if current_value != new_value:
                        setattr(service, field, new_value)
                        has_changes = True
                        changed_fields.append(field)
                except Exception as e:
                    log.error(
                        f"Command: update_services_seo | Action: FieldError | slug={slug} | field={field} | error={e}"
                    )
                    continue

            if has_changes:
                service.save()
                updated_count += 1
                log.info(f"Command: update_services_seo | Action: Updated | slug={slug} | fields={changed_fields}")
                self.stdout.write(self.style.SUCCESS(f"  [UPDATE] Service SEO: {slug}"))
                # Invalidate cache
                cache.delete_many([f"service_detail_{service.slug}", f"category_detail_{service.category.slug}"])
            else:
                skipped_count += 1

        log.info(f"Command: update_services_seo | Action: Success | updated={updated_count} | skipped={skipped_count}")
        self.stdout.write(self.style.SUCCESS(f"\nFinished: {updated_count} updated, {skipped_count} skipped."))
