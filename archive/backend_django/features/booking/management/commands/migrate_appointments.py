from core.logger import log
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

        log.info(
            f"Command: migrate_appointments | Action: Start | old_pk={old_pk} | new_pk={new_pk} | dry_run={dry_run}"
        )

        Service = apps.get_model("main", "Service")
        Appointment = apps.get_model("booking", "Appointment")

        try:
            # Check if both services exist
            if not Service.objects.filter(pk=old_pk).exists() or not Service.objects.filter(pk=new_pk).exists():
                log.error(
                    f"Command: migrate_appointments | Action: Failed | error=ServiceNotFound | old_pk={old_pk} | new_pk={new_pk}"
                )
                self.stdout.write(self.style.ERROR(f"One of the services (ID {old_pk} or {new_pk}) does not exist."))
                return

            new_service = Service.objects.get(pk=new_pk)
        except Exception as e:
            log.error(f"Command: migrate_appointments | Action: Failed | error={e}")
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
            return

        appointments = Appointment.objects.filter(service_id=old_pk)
        count = appointments.count()

        if count == 0:
            log.warning(f"Command: migrate_appointments | Action: NoAppointmentsFound | old_pk={old_pk}")
            self.stdout.write(self.style.WARNING(f"No appointments found for service ID {old_pk}."))
            return

        log.debug(f"Command: migrate_appointments | Action: FoundAppointments | count={count}")

        try:
            with transaction.atomic():
                for appt in appointments:
                    if dry_run:
                        log.debug(
                            f"Command: migrate_appointments | Action: DryRun | appt_id={appt.id} | client={appt.client}"
                        )
                    else:
                        appt.service = new_service
                        if update_price:
                            appt.price = new_service.price
                            appt.duration_minutes = new_service.duration
                            log.debug(
                                f"Command: migrate_appointments | Action: UpdateFull | appt_id={appt.id} | price={appt.price}"
                            )
                        else:
                            log.debug(f"Command: migrate_appointments | Action: UpdateServiceOnly | appt_id={appt.id}")

                        appt.save(update_fields=["service", "price", "duration_minutes", "updated_at"])

            if dry_run:
                log.info("Command: migrate_appointments | Action: DryRunComplete")
            else:
                log.info(f"Command: migrate_appointments | Action: Success | migrated_count={count}")
                self.stdout.write(self.style.SUCCESS(f"\nSuccessfully migrated {count} appointments."))

        except Exception as e:
            log.error(f"Command: migrate_appointments | Action: Failed | error={e}")
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
            raise
