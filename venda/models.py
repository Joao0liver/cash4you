from django.core.validators import MinValueValidator
from django.db import models

class Venda(models.Model):

    criada_em = models.DateTimeField(auto_now_add=True)
    nome_cliente = models.CharField(max_length=120, blank=True, default="")
    telefone_whatsapp = models.CharField(max_length=20, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ("-criada_em", "-id")

    def __str__(self):
        return f"Venda #{self.pk} - R$ {self.total}"

class PagamentoVenda(models.Model):

    class FormaPagamento(models.TextChoices):
        DINHEIRO = "dinheiro", "Dinheiro"
        CREDITO = "credito", "Cartão de crédito"
        DEBITO = "debito", "Cartão de débito"
        PIX = "pix", "Pix"

    venda = models.ForeignKey(Venda, related_name="pagamentos", on_delete=models.CASCADE)
    forma_pagamento = models.CharField(max_length=10, choices=FormaPagamento.choices)
    valor = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    valor_recebido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    troco = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return f"{self.get_forma_pagamento_display()} - R$ {self.valor}"
