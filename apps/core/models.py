from django.db import models


class FAQ(models.Model):
    question = models.CharField(max_length=500, verbose_name="Pregunta")
    answer = models.TextField(verbose_name="Respuesta")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")
    is_active = models.BooleanField(default=True, verbose_name="Activa")

    class Meta:
        verbose_name = "Pregunta Frecuente"
        verbose_name_plural = "Preguntas Frecuentes"
        ordering = ["order"]

    def __str__(self):
        return self.question
