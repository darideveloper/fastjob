"""
Admin-side GDPR deletion. Usage:

    python manage.py delete_user --email ana@example.com

Requires --yes to bypass the interactive confirmation.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Permanently delete a user and all associated data (CVs, logs, OAuth tokens)."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="Email of the user to delete")
        parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")

    def handle(self, *args, **opts):
        User = get_user_model()
        email = opts["email"].strip().lower()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise CommandError(f"No user with email {email!r}.")

        if not opts["yes"]:
            answer = input(f"Delete {user.email} (id={user.pk}) and all their data? [y/N] ")
            if answer.strip().lower() not in ("y", "yes"):
                self.stdout.write(self.style.WARNING("Aborted."))
                return

        cv_count = user.cvs.count()
        log_count = user.mailing_logs.count()
        # Atomic: a SIGTERM during the CV loop must not leave a user row
        # without its associated CVs. Either the whole account is gone
        # or nothing changed.
        with transaction.atomic():
            for cv in user.cvs.all():
                cv.delete()  # pre_delete signal removes the S3 object too.
            user.delete()

        self.stdout.write(self.style.SUCCESS(
            f"Deleted user {email} — removed {cv_count} CV(s), {log_count} mailing log(s)."
        ))
