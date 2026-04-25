from django.db import migrations
from decimal import Decimal


PACKAGES = [
    {
        "name": "Starter",
        "description": "Perfecto para probar la plataforma",
        "price_eur": Decimal("9.99"),
        "credits": 50,
        "order": 1,
    },
    {
        "name": "Pro",
        "description": "El paquete más popular para búsqueda activa",
        "price_eur": Decimal("29.99"),
        "credits": 200,
        "order": 2,
    },
    {
        "name": "Elite",
        "description": "Máximo alcance para profesionales senior",
        "price_eur": Decimal("69.99"),
        "credits": 600,
        "order": 3,
    },
]


def seed_packages(apps, schema_editor):
    CreditPackage = apps.get_model("payments", "CreditPackage")
    for p in PACKAGES:
        CreditPackage.objects.get_or_create(
            name=p["name"],
            defaults={
                "description": p["description"],
                "price_eur": p["price_eur"],
                "credits": p["credits"],
                "order": p["order"],
                "is_active": True,
            },
        )


def unseed_packages(apps, schema_editor):
    CreditPackage = apps.get_model("payments", "CreditPackage")
    CreditPackage.objects.filter(name__in=[p["name"] for p in PACKAGES]).delete()


class Migration(migrations.Migration):
    dependencies = [("payments", "0001_initial")]
    operations = [migrations.RunPython(seed_packages, unseed_packages)]
