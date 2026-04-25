from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("mailing", "0002_seed_templates"),
        ("accounts", "0002_cv_model_and_customer"),
    ]

    operations = [
        migrations.AddField(
            model_name="mailinglog",
            name="cv",
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="mailing_logs",
                to="accounts.cv",
            ),
        ),
    ]
