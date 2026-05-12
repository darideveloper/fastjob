from django.core.management.base import BaseCommand
from apps.companies.models import Company, Area, Location, Blacklist, CompanyImportBatch


class Command(BaseCommand):
    help = "Deletes all company data from the database (Companies, Areas, Locations, etc.)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("\n[1/5] Cleaning up Companies..."))
        try:
            count_before = Company.objects.count()
            deleted, details = Company.objects.all().delete()
            num_deleted = details.get("companies.Company", 0)
            self.stdout.write(f"  - Records found: {count_before}")
            self.stdout.write(f"  - Records deleted: {num_deleted}")
            self.stdout.write(self.style.SUCCESS("  - OK."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"  - ERROR deleting companies: {e}"))

        self.stdout.write(self.style.WARNING("\n[2/5] Cleaning up Sectors (Areas)..."))
        try:
            count_before = Area.objects.count()
            deleted, details = Area.objects.all().delete()
            num_deleted = details.get("companies.Area", 0)
            self.stdout.write(f"  - Records found: {count_before}")
            self.stdout.write(f"  - Records deleted: {num_deleted}")
            self.stdout.write(self.style.SUCCESS("  - OK."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"  - ERROR deleting sectors: {e}"))

        self.stdout.write(self.style.WARNING("\n[3/5] Cleaning up Locations..."))
        try:
            count_before = Location.objects.count()
            deleted, details = Location.objects.all().delete()
            num_deleted = details.get("companies.Location", 0)
            self.stdout.write(f"  - Records found: {count_before}")
            self.stdout.write(f"  - Records deleted: {num_deleted}")
            self.stdout.write(self.style.SUCCESS("  - OK."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"  - ERROR deleting locations: {e}"))

        self.stdout.write(self.style.WARNING("\n[4/5] Cleaning up Blacklist..."))
        try:
            count_before = Blacklist.objects.count()
            deleted, details = Blacklist.objects.all().delete()
            num_deleted = details.get("companies.Blacklist", 0)
            self.stdout.write(f"  - Records found: {count_before}")
            self.stdout.write(f"  - Records deleted: {num_deleted}")
            self.stdout.write(self.style.SUCCESS("  - OK."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"  - ERROR deleting blacklist: {e}"))

        self.stdout.write(self.style.WARNING("\n[5/5] Cleaning up Import Batches..."))
        try:
            count_before = CompanyImportBatch.objects.count()
            deleted, details = CompanyImportBatch.objects.all().delete()
            num_deleted = details.get("companies.CompanyImportBatch", 0)
            self.stdout.write(f"  - Records found: {count_before}")
            self.stdout.write(f"  - Records deleted: {num_deleted}")
            self.stdout.write(self.style.SUCCESS("  - OK."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"  - ERROR deleting import batches: {e}"))

        self.stdout.write(self.style.SUCCESS("\n--- Cleanup process finished ---\n"))
