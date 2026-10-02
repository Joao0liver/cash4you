from django.contrib import admin

from .models import ContaPagar


@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    list_display = ("descricao", "valor", "vencimento", "paga")
    list_filter = ("paga", "vencimento")
    search_fields = ("descricao",)
