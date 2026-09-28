from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):

    # Cria os grupos padrão do Cash4You e atribui suas permissões
    def handle(self, *args, **kwargs):

        grupos = [
            "Administrador",
            "Gerente",
            "Funcionário",
        ]

        grupos_criados = {}

        for nome in grupos:
            grupo, criado = Group.objects.get_or_create(name=nome)

            grupos_criados[nome] = grupo

            if criado:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Grupo "{nome}" criado com sucesso.'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Grupo "{nome}" já existe.'
                    )
                )

        # PERMISSÕES
        administrador = grupos_criados["Administrador"]
        gerente = grupos_criados["Gerente"]
        funcionario = grupos_criados["Funcionário"]

        # Administrador
        administrador.permissions.set(
            Permission.objects.filter(
                content_type__app_label__in=[
                    "usuario",
                    "produto",
                    "servico",
                    "cliente",
                ]
            )
        )

        # Gerente
        gerente.permissions.set(
            Permission.objects.filter(
                content_type__app_label__in=[
                    "produto",
                    "servico",
                    "cliente",
                ]
            )
        )

        # Remove permissões de exclusão do Gerente
        gerente.permissions.remove(
            *Permission.objects.filter(
                content_type__app_label__in=[
                    "produto",
                    "servico",
                    "cliente",
                ],
                codename__startswith="delete_",
            )
        )

        # Funcionário
        funcionario.permissions.set(
            Permission.objects.filter(
                content_type__app_label__in=[
                    "produto",
                    "servico",
                ],
                codename__startswith="view_",
            )
            |
            Permission.objects.filter(
                content_type__app_label="cliente",
                codename__in=[
                    "view_cliente",
                    "add_cliente",
                    "change_cliente",
                ],
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Permissões configuradas com sucesso."
            )
        )