from django.core.validators import MinValueValidator
from django.db import models


class Venda(models.Model):
    class FormaPagamento(models.TextChoices):
        DINHEIRO = "dinheiro", "Dinheiro"
        CREDITO = "credito", "Cartão de crédito"
        DEBITO = "debito", "Cartão de débito"
        PIX = "pix", "Pix"

    criada_em = models.DateTimeField(auto_now_add=True)
    forma_pagamento = models.CharField(max_length=10, choices=FormaPagamento.choices)
    telefone_whatsapp = models.CharField(max_length=20, blank=True)
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    valor_recebido = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    troco = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        ordering = ("-criada_em", "-id")

    def __str__(self):
        return f"Venda #{self.pk} - R$ {self.total}"


class ItemVenda(models.Model):
    class Tipo(models.TextChoices):
        PRODUTO = "produto", "Produto"
        SERVICO = "servico", "Serviço"

    venda = models.ForeignKey(Venda, on_delete=models.CASCADE, related_name="itens")
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    produto = models.ForeignKey(
        "produto.Produto",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="itens_vendidos",
    )
    servico = models.ForeignKey(
        "servico.Servico",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="itens_vendidos",
    )
    descricao = models.CharField(max_length=100)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return f"{self.descricao} x {self.quantidade}"
