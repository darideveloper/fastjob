from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mailing', '0011_systemsettings_save_emails_to_sent_folder'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemsettings',
            name='displayed_sends_floor',
            field=models.IntegerField(
                default=0,
                verbose_name='Mínimo de envíos mostrados',
                help_text=(
                    'Si el número real de envíos exitosos es menor que este valor, '
                    'se mostrará este valor en la página de paquetes. '
                    'Usar 0 para mostrar siempre el valor real.'
                ),
            ),
        ),
    ]
