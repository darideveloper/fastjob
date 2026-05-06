from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("companies", "0008_normalize_blacklist_emails"),
    ]

    operations = [
        migrations.AddField(
            model_name="companyimportbatch",
            name="blacklisted_skipped",
            field=models.IntegerField(default=0),
        ),
    ]
