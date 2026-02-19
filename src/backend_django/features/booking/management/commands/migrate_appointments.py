from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Migrate appointments from one Service ID to another (e.g. from ID 1 to ID 200)"

    def add_arguments(self, parser):
        parser.add_argument("old_pk", type=int, help="ID of the OLD service (to migrate FROM)")
        parser.add_argument("new_pk", type=int, help="ID of the NEW service (to migrate TO)")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would happen without making changes",
        )
        parser.add_argument(
            "--update-price",
            action="store_true",
            help="Update the appointment price and duration to match the new service",
        )

    def handle(self, *args, **options):
        old_pk = options["old_pk"]
        new_pk = options["new_pk"]
        dry_run = options["dry_run"]
        update_price = options["update_price"]

        Service = apps.get_model("main", "Service")
        Appointment = apps.get_model("booking", "Appointment")

        try:
            old_service = Service.objects.get(pk=old_pk)
            new_service = Service.objects.get(pk=new_pk)
        except Service.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"One of the services (ID {old_pk} or {new_pk}) does not exist."))
            return

        self.stdout.write(
            f"Migrating appointments from '{old_service.title}' (ID {old_pk}) -> '{new_service.title}' (ID {new_pk})"
        )

        appointments = Appointment.objects.filter(service_id=old_pk)
        count = appointments.count()

        if count == 0:
            self.stdout.write(self.style.WARNING(f"No appointments found for service ID {old_pk}."))
            return

        self.stdout.write(f"Found {count} appointments to migrate.")

        with transaction.atomic():
            for appt in appointments:
                if dry_run:
                    self.stdout.write(f"  [DRY-RUN] Will update appointment #{appt.id} (Client: {appt.client})")
                else:
                    appt.service = new_service
                    if update_price:
                        appt.price = new_service.price
                        appt.duration_minutes = new_service.duration
                        self.stdout.write(f"  [UPDATE] Appt #{appt.id}: Service changed. Price/Duration updated.")
                    else:
                        self.stdout.write(f"  [UPDATE] Appt #{appt.id}: Service changed only.")

                    appt.save(update_fields=["service", "price", "duration_minutes", "updated_at"])

        if dry_run:
            self.stdout.write(self.style.SUCCESS("\nDry run complete. No changes made."))
        else:
            self.stdout.write(self.style.SUCCESS(f"\nSuccessfully migrated {count} appointments."))
