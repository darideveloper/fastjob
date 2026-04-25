from django.db import models
from django.utils import timezone


class Company(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=300)
    area = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=200, blank=True)
    last_received_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} <{self.email}>"


class Blacklist(models.Model):
    email = models.EmailField(unique=True)
    added_at = models.DateTimeField(default=timezone.now)
    reason = models.CharField(max_length=100, default="unsubscribe")

    class Meta:
        verbose_name = "Lista Negra"
        verbose_name_plural = "Lista Negra"
        ordering = ["-added_at"]

    def __str__(self):
        return self.email
