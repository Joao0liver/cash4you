from django.contrib import admin

from .models import VendaItem

@admin.register(VendaItem)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "item",
        "quantidade",
        "valor_unitario",
    )
