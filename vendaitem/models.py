from django.db import models
from catalogo.models import Item
from venda.models import Venda
from django.core.validators import MinValueValidator

class VendaItem(models.Model):

    venda = models.ForeignKey(Venda, on_delete=models.PROTECT, related_name="itens")
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="venda_itens")
    quantidade = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.item} - {self.quantidade}x"
