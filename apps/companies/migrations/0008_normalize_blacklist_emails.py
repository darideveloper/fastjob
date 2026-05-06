from django.db import migrations


def normalize_blacklist_emails(apps, schema_editor):
    Blacklist = apps.get_model("companies", "Blacklist")
    db_alias = schema_editor.connection.alias

    # Process rows whose email has uppercase chars.
    for row in Blacklist.objects.using(db_alias).extra(
        where=["email != LOWER(email)"]
    ):
        normalized = row.email.lower()
        # If a lowercase duplicate already exists, keep the earlier one.
        existing = (
            Blacklist.objects.using(db_alias)
            .filter(email=normalized)
            .exclude(pk=row.pk)
            .first()
        )
        if existing:
            if existing.added_at <= row.added_at:
                row.delete()
            else:
                existing.delete()
                row.email = normalized
                row.save(update_fields=["email"])
        else:
            row.email = normalized
            row.save(update_fields=["email"])


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0007_companyimportbatch"),
    ]

    operations = [
        migrations.RunPython(normalize_blacklist_emails, migrations.RunPython.noop),
    ]
