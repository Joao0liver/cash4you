from django.core.validators import MinValueValidator
from django.db import models


class ContaPagar(models.Model):
    descricao = models.CharField(max_length=160)
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    vencimento = models.DateField()
    paga = models.BooleanField(default=False)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("vencimento", "descricao", "id")
        verbose_name = "conta a pagar"
        verbose_name_plural = "contas a pagar"

    def __str__(self):
        return self.descricao
