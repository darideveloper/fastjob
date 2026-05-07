"""
Run once after migrations to register the company-import purge periodic task in Celery Beat.
Usage: python manage.py setup_company_import_periodics
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask


class Command(BaseCommand):
    help = "Create or update the company import purge periodic task in django-celery-beat."

    def handle(self, *args, **options):
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=30,
            hour=3,
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
            defaults={"timezone": "Europe/Madrid"},
        )
        task, created = PeriodicTask.objects.update_or_create(
            name="purge-stale-company-import-files",
            defaults={
                "task": "apps.companies.tasks.purge_stale_company_import_files",
                "crontab": schedule,
                "enabled": True,
            },
        )
        verb = "Creada" if created else "Actualizada"
        self.stdout.write(self.style.SUCCESS(f"{verb} tarea periódica: {task.name}"))
