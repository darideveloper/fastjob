"""
Multi-CV refactor + Stripe customer ID.

Creates the new CV model, migrates any existing User.cv_file into a CV row,
wires User.active_cv, adds User.stripe_customer_id, then drops the legacy
cv_file / cv_updated_at fields.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_existing_cvs(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    CV = apps.get_model("accounts", "CV")
    for user in User.objects.exclude(cv_file="").exclude(cv_file__isnull=True):
        cv = CV.objects.create(
            user=user,
            file=user.cv_file.name if hasattr(user.cv_file, "name") else user.cv_file,
            name="",
        )
        user.active_cv = cv
        user.save(update_fields=["active_cv"])


def noop_reverse(apps, schema_editor):
    # We don't restore cv_file; roll forward instead.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CV",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="cvs/")),
                ("name", models.CharField(blank=True, max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="cvs",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={"verbose_name": "CV", "verbose_name_plural": "CVs", "ordering": ["-created_at"]},
        ),
        migrations.AddField(
            model_name="user",
            name="active_cv",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="accounts.cv",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="stripe_customer_id",
            field=models.CharField(blank=True, db_index=True, max_length=200, default=""),
            preserve_default=False,
        ),
        migrations.RunPython(migrate_existing_cvs, noop_reverse),
        migrations.RemoveField(model_name="user", name="cv_file"),
        migrations.RemoveField(model_name="user", name="cv_updated_at"),
    ]
