from django.db import models


class CreditPackage(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price_eur = models.DecimalField(max_digits=8, decimal_places=2)
    credits = models.IntegerField(verbose_name="Envíos")
    stripe_price_id = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Paquete de Envíos"
        verbose_name_plural = "Paquetes de Envíos"
        ordering = ["order", "price_eur"]

    def __str__(self):
        return f"{self.name} — {self.credits} envíos por {self.price_eur}€"

    @property
    def price_cents(self):
        return int(self.price_eur * 100)


class StripePayment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        COMPLETED = "completed", "Completado"
        FAILED = "failed", "Fallido"

    user = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, related_name="payments", verbose_name="Usuario")
    package = models.ForeignKey(CreditPackage, on_delete=models.SET_NULL, null=True, verbose_name="Paquete")
    stripe_session_id = models.CharField(max_length=300, unique=True, verbose_name="ID de sesión Stripe")
    stripe_payment_intent = models.CharField(max_length=300, blank=True, verbose_name="Payment intent Stripe")
    amount_eur = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Importe (€)")
    credits_granted = models.IntegerField(default=0, verbose_name="Envíos otorgados")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, verbose_name="Estado")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Completado el")

    class Meta:
        verbose_name = "Pago Stripe"
        verbose_name_plural = "Pagos Stripe"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.amount_eur}€ ({self.status})"
