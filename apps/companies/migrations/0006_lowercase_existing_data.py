from django.db import migrations, models

def lowercase_data(apps, schema_editor):
    Area = apps.get_model('companies', 'Area')
    Location = apps.get_model('companies', 'Location')
    Company = apps.get_model('companies', 'Company')
    User = apps.get_model('accounts', 'User')

    def merge_taxonomy(Model, FK_field_company, FK_field_user):
        objs = list(Model.objects.all())
        seen = {}
        for obj in objs:
            lower_name = obj.name.lower()
            if lower_name in seen:
                # Merge into existing
                target = seen[lower_name]
                Company.objects.filter(**{FK_field_company: obj}).update(**{FK_field_company: target})
                User.objects.filter(**{FK_field_user: obj}).update(**{FK_field_user: target})
                obj.delete()
            else:
                if obj.name != lower_name:
                    obj.name = lower_name
                    obj.save()
                seen[lower_name] = obj

    merge_taxonomy(Area, 'area', 'area_filter')
    merge_taxonomy(Location, 'location', 'location_filter')

    # Lowercase Company fields
    for company in Company.objects.all():
        company.email = company.email.lower()
        company.name = company.name.lower()
        # New fields might be empty but calling lower() on "" is fine
        company.address = company.address.lower()
        company.province = company.province.lower()
        company.community = company.community.lower()
        company.website = company.website.lower()
        company.save()

class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0005_company_address_company_community_company_fax_and_more'),
        ('accounts', '0008_remove_user_area_filter_fk_and_more'), # Ensure User model is ready
    ]

    operations = [
        migrations.RunPython(lowercase_data, reverse_code=migrations.RunPython.noop),
    ]
