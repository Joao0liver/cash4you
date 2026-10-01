from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Produto(models.Model):

    descricao = models.CharField(max_length=100)
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2)
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade = models.IntegerField()
    despesas_variaveis_percentual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    lucro_desejado_percentual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    def __str__(self):
        return self.descricao