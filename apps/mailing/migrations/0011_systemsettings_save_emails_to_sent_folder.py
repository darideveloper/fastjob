from django.db import migrations, models


def copy_save_emails_setting(apps, schema_editor):
    """Copy save_emails_to_sent_folder from core_systemconfig to mailing_systemsettings."""
    db = schema_editor.connection.alias
    try:
        SystemConfig = apps.get_model("core", "SystemConfig")
        config = SystemConfig.objects.using(db).filter(pk=1).first()
        if config is None:
            return
        SystemSettings = apps.get_model("mailing", "SystemSettings")
        obj, _ = SystemSettings.objects.using(db).get_or_create(pk=1)
        obj.save_emails_to_sent_folder = config.save_emails_to_sent_folder
        obj.save()
    except Exception:
        pass


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("mailing", "0010_normalize_mailing_log_emails"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemsettings",
            name="save_emails_to_sent_folder",
            field=models.BooleanField(
                default=False,
                help_text="Si está activado, los correos enviados se guardarán en la carpeta 'Enviados' del usuario.",
                verbose_name="Guardar en carpeta Enviados",
            ),
        ),
        migrations.RunPython(copy_save_emails_setting, noop),
    ]
