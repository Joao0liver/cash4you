from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario

@admin.register(Usuario) # Decorator python: "Registre o modelo Usuario no painel administrativo e use a classe UsuarioAdmin para configurá-lo."
class UsuarioAdmin(UserAdmin):

    # Define o atributo de ordenação
    ordering = ("nome",)

    # Informações qeu serão dispostas no painel administrativo do django
    list_display = (
        "id",
        "nome",
        "email",
        "is_active",
        "is_staff",
    )

    # Quais atributos podem ser buscados
    search_fields = (
        "nome",
        "email",
    )

    # Define a disposição das informações em visualização/edição
    fieldsets = (
        (None, {
            "fields": ("email", "password"),
        }), # Título e campos
        ("Informações pessoais", {
            "fields": ("nome",),
        }),
        ("Permissões", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            ),
        }),
        ("Datas importantes", {
            "fields": (
                "last_login",
                "date_joined",
            ),
        }),
    )

    # Controla quais informações são solicitadas na tela de criação de usuários
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "nome",
                "password1", # Senha
                "password2", # Confirmar senha
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
            ),
        }),
    )