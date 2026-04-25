"""
Run once after migrations: creates the Celery beat periodic task in the DB.
Usage: python manage.py setup_periodic_tasks
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import IntervalSchedule, PeriodicTask


class Command(BaseCommand):
    help = "Create or update the mailing periodic task in django-celery-beat."

    def handle(self, *args, **options):
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.MINUTES,
        )
        task, created = PeriodicTask.objects.update_or_create(
            name="process-mailing-queue",
            defaults={
                "task": "apps.mailing.tasks.process_mailing_queue",
                "interval": schedule,
                "enabled": True,
            },
        )
        verb = "Creada" if created else "Actualizada"
        self.stdout.write(self.style.SUCCESS(f"{verb} tarea periódica: {task.name}"))
