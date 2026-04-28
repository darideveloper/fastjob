"""C5 (security-fixes.md) data-migration guard.

Runs immediately before the schema migration that adds `unique=True` to
`User.email`. If two or more users share an email at this point, the
schema migration would crash with an `IntegrityError` and leave the DB
in a half-migrated state. This guard detects the condition first and
raises a clear, actionable error so ops can dedupe the rows manually.
"""
from django.db import migrations
from django.db.models import Count


def assert_no_duplicate_emails(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    duplicates = (
        User.objects.values("email")
        .annotate(n=Count("id"))
        .filter(n__gt=1)
        .order_by("-n")
    )
    if duplicates.exists():
        offenders = ", ".join(
            f"{row['email']} (×{row['n']})" for row in duplicates[:10]
        )
        raise RuntimeError(
            "Cannot apply unique constraint on User.email: duplicate rows exist. "
            f"Affected emails: {offenders}. Resolve manually before re-running."
        )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_cv_model_and_customer"),
    ]

    operations = [
        migrations.RunPython(
            assert_no_duplicate_emails,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
