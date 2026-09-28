from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):

    ordering = ("nome",)

    list_display = (
        "nome",
        "email",
        "is_active",
        "is_staff",
    )

    search_fields = (
        "nome",
        "email",
    )

    fieldsets = (
        (None, {
            "fields": ("email", "password"),
        }),
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

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "nome",
                "password1",
                "password2",
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
            ),
        }),
    )