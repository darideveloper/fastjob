from django.db import migrations, models
from django.db.models import Sum


def populate_total_purchased_credits(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    StripePayment = apps.get_model("payments", "StripePayment")

    for user in User.objects.all():
        total = StripePayment.objects.filter(
            user=user,
            status="completed"
        ).aggregate(total=Sum("credits_granted"))["total"] or 0
        
        user.total_purchased_credits = total
        user.save(update_fields=["total_purchased_credits"])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_user_total_purchased_credits'),
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_total_purchased_credits, reverse_code=migrations.RunPython.noop),
    ]
