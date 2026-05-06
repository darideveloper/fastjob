from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mailing", "0005_systemsettings_max_emails_per_day_per_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="mailinglog",
            name="unsubscribed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
