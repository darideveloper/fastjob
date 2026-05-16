from django.db import models


class SystemConfig(models.Model):
    save_emails_to_sent_folder = models.BooleanField(
        default=False,
        verbose_name="Guardar en carpeta Enviados",
        help_text="Si está desactivado, los correos enviados no se guardarán en la carpeta 'Enviados'.",
    )

    class Meta:
        verbose_name = "Configuración General"
        verbose_name_plural = "Configuración General"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # Singleton cannot be deleted

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Configuración General"
