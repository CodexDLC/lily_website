import json

from core.logger import log
from django.conf import settings
from django.core.management.base import BaseCommand
from features.system.models.seo import StaticPageSeo


class Command(BaseCommand):
    help = "Update SEO fields for Static Pages from static_pages_seo.json"

    def handle(self, *args, **options):
        log.info("Command: update_static_seo | Action: Start")

        # Read specific file for static pages
        file_path = settings.BASE_DIR / "features" / "system" / "fixtures" / "seo" / "static_pages_seo.json"
        log.debug(f"Command: update_static_seo | Action: LoadFixture | path={file_path}")

        if not file_path.exists():
            log.error(f"Command: update_static_seo | Action: Failed | error=File not found | path={file_path}")
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        try:
            with open(file_path, encoding="utf-8") as f:
                all_seo_data = json.load(f)
        except Exception as e:
            log.error(f"Command: update_static_seo | Action: Failed | error=JSONError | message={e}")
            self.stdout.write(self.style.ERROR(f"Error reading JSON: {e}"))
            return

        updated_count = 0
        skipped_count = 0

        log.debug(f"Command: update_static_seo | Action: ProcessingPages | count={len(all_seo_data)}")

        for page_key, new_data in all_seo_data.items():
            # Get or create SEO object for the page
            seo_obj, created = StaticPageSeo.objects.get_or_create(page_key=page_key)

            has_changes = False
            changed_fields = []
            for field, new_value in new_data.items():
                try:
                    current_value = getattr(seo_obj, field, None)
                    if current_value != new_value:
                        setattr(seo_obj, field, new_value)
                        has_changes = True
                        changed_fields.append(field)
                except Exception as e:
                    log.error(
                        f"Command: update_static_seo | Action: FieldError | page_key={page_key} | field={field} | error={e}"
                    )
                    continue

            if has_changes:
                seo_obj.save()
                updated_count += 1
                status = "CREATED" if created else "UPDATED"
                log.info(
                    f"Command: update_static_seo | Action: {status} | page_key={page_key} | fields={changed_fields}"
                )
                self.stdout.write(self.style.SUCCESS(f"  [{status}] Static SEO: {page_key}"))
            else:
                skipped_count += 1

        log.info(f"Command: update_static_seo | Action: Success | updated={updated_count} | skipped={skipped_count}")
        self.stdout.write(self.style.SUCCESS(f"\nFinished: {updated_count} updated, {skipped_count} skipped."))
