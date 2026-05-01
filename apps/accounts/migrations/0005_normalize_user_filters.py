from django.db import migrations


def normalize_user_filters(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Company = apps.get_model("companies", "Company")

    valid_areas = {
        v.strip().lower()
        for v in Company.objects.exclude(area="").values_list("area", flat=True).distinct()
        if v.strip()
    }
    valid_locations = {
        v.strip().lower()
        for v in Company.objects.exclude(location="").values_list("location", flat=True).distinct()
        if v.strip()
    }

    to_update = []
    for user in User.objects.exclude(area_filter="", location_filter="").iterator():
        changed = False
        if user.area_filter and user.area_filter.strip().lower() not in valid_areas:
            user.area_filter = ""
            changed = True
        if user.location_filter and user.location_filter.strip().lower() not in valid_locations:
            user.location_filter = ""
            changed = True
        if changed:
            to_update.append(user)

    if to_update:
        User.objects.bulk_update(to_update, ["area_filter", "location_filter"])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_alter_user_email"),
        ("companies", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(normalize_user_filters, migrations.RunPython.noop),
    ]
