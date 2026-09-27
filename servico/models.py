from django.db import models

class Servico(models.Model):

    descricao = models.CharField(max_length=100)
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.descricao