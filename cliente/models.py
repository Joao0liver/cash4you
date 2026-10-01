from django.core.exceptions import ValidationError
from django.db import models


def _cpf_valido(cpf):
    if len(set(cpf)) == 1:
        return False

    numeros = [int(digito) for digito in cpf]
    primeiro_digito = (sum(
        numero * peso for numero, peso in zip(numeros[:9], range(10, 1, -1))
    ) * 10) % 11 % 10
    segundo_digito = (sum(
        numero * peso for numero, peso in zip(numeros[:9] + [primeiro_digito], range(11, 1, -1))
    ) * 10) % 11 % 10

    return numeros[9:] == [primeiro_digito, segundo_digito]


class Cliente(models.Model):

    nome = models.CharField(max_length=100, blank=False, null=False)
    cpf = models.CharField(max_length=11, blank=False, null=False)
    telefone = models.CharField(max_length=11, blank=False, null=False)

    def clean(self):
        super().clean()
        self.nome = self.nome.strip()
        self.cpf = self.cpf.strip()
        self.telefone = self.telefone.strip()

        if not self.nome:
            raise ValidationError({"nome": "O nome não pode estar vazio."})

        if len(self.cpf) != 11 or not self.cpf.isdigit():
            raise ValidationError({"cpf": "O CPF deve conter exatamente 11 dígitos."})

        if not _cpf_valido(self.cpf):
            raise ValidationError({"cpf": "Informe um CPF válido."})

        if len(self.telefone) < 10 or not self.telefone.isdigit():
            raise ValidationError({"telefone": "O telefone deve conter apenas números."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome