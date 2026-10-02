from django.contrib import admin

from .models import ContaPagar, Funcionario


@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    list_display = ("descricao", "valor", "vencimento", "paga")
    list_filter = ("paga", "vencimento")
    search_fields = ("descricao",)


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ("nome", "funcao")
    search_fields = ("nome", "funcao")
