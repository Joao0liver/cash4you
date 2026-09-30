from django.contrib import admin

from .models import Item, Produto, Servico

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "descricao",
        "preco_venda",
    )

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "descricao",
        "preco_venda",
        "preco_custo",
        "quantidade",
    )

@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "descricao",
        "preco_venda",
    )