from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        ("mailing", "0011_systemsettings_save_emails_to_sent_folder"),
    ]

    operations = [
        migrations.DeleteModel(
            name="SystemConfig",
        ),
    ]
