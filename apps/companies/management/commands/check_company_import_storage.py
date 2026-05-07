"""
Check that COMPANY_IMPORT_LOCAL_PATH exists, is a directory, and is writable.
Usage: python manage.py check_company_import_storage
Exit code 0 = OK, 1 = warning (path issue).
"""
import os

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Assert COMPANY_IMPORT_LOCAL_PATH is a writable directory."

    def handle(self, *args, **options):
        path = settings.COMPANY_IMPORT_LOCAL_PATH
        issues = []

        if not os.path.exists(path):
            issues.append(f"Path does not exist: {path}")
        elif not os.path.isdir(path):
            issues.append(f"Path is not a directory: {path}")
        elif not os.access(path, os.W_OK):
            issues.append(f"Path is not writable: {path}")

        if issues:
            for issue in issues:
                self.stderr.write(self.style.WARNING(f"[WARN] {issue}"))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS(f"[OK] COMPANY_IMPORT_LOCAL_PATH={path}"))
