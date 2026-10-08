from django.db import models
from django.core.validators import MinValueValidator

class DadosEstabelecimento(models.Model):

    nome = models.CharField(max_length=120, blank=True, default="")
    horario_funcionamento = models.CharField(max_length=120, blank=True, default="")
    endereco = models.CharField(max_length=255, blank=True, default="")
    limite_gastos = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Margem máxima de gastos",
    )

    def __str__(self):
        return self.nome or "Dados do estabelecimento"
