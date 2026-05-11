from django.db import migrations

def migrate_filters(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    for user in User.objects.all():
        if user.area_filter_id:
            user.area_filters.add(user.area_filter_id)
        if user.location_filter_id:
            user.location_filters.add(user.location_filter_id)

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_user_area_filters_user_location_filters'),
    ]

    operations = [
        migrations.RunPython(migrate_filters, migrations.RunPython.noop),
    ]
