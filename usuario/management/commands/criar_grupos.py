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
                    "catalogo",
                    "cliente",
                    "venda",
                    "vendaitem",
                    "agenda",
                ]
            )
        )

        # Gerente
        gerente.permissions.set(
            Permission.objects.filter(
                content_type__app_label__in=[
                    "catalogo"
                    "cliente",
                    "agenda",
                    "venda",
                    "vendaitem",
                ]
            )
        )
        # Remove permissões de exclusão do Gerente
        gerente.permissions.remove(
            *Permission.objects.filter(
                content_type__app_label__in=[
                    "catalogo"
                    "cliente",
                    "venda",
                    "vendaitem",
                ],
                codename__startswith="delete_",
            )
        )

        # Funcionário
        funcionario.permissions.set(
            Permission.objects.filter(
                content_type__app_label__in=[
                    "catalogo"
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
            |
            Permission.objects.filter(
                content_type__app_label="venda",
                codename__in=[
                    "view_venda",
                    "add_venda",
                ],
            )
            |
            Permission.objects.filter(
                content_type__app_label="vendaitem",
                codename__in=[
                    "view_vendaitem",
                    "add_vendaitem",
                ],
            )
            |
            Permission.objects.filter(
                content_type__app_label__in=[
                    "agenda",
                ]
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Permissões configuradas com sucesso."
            )
        )