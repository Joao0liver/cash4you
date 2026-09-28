from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = "Cria os grupos padrão do Cash4You."

    def handle(self, *args, **kwargs):
        grupos = [
            "Administrador",
            "Gerente",
            "Funcionário",
        ]

        for nome in grupos:
            grupo, criado = Group.objects.get_or_create(name=nome)

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