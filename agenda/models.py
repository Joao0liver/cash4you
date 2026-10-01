from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import models
import re


class Agendamento(models.Model):
    data = models.DateField()
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    servicos = models.ManyToManyField(
        "servico.Servico",
        blank=True,
        related_name="agendamentos",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("data", "nome", "id")

    @property
    def whatsapp_numero(self):
        numero = re.sub(r"\D", "", self.telefone)
        if len(numero) in (10, 11):
            return f"55{numero}"
        return numero

    def __str__(self):
        return f"{self.nome} - {self.data:%d/%m/%Y}"


class HorarioAgendado(models.Model):
    agendamento = models.ForeignKey(
        Agendamento,
        on_delete=models.CASCADE,
        related_name="horarios",
    )
    data = models.DateField()
    inicio = models.TimeField()
    fim = models.TimeField()

    class Meta:
        ordering = ("inicio",)
        constraints = [
            models.UniqueConstraint(
                fields=("data", "inicio"),
                name="agenda_horario_data_inicio_unico",
            )
        ]

    def clean(self):
        super().clean()
        inicio = datetime.combine(self.data, self.inicio)
        fim = datetime.combine(self.data, self.fim)
        if fim - inicio != timedelta(minutes=30):
            raise ValidationError({"fim": "O bloco deve ter exatamente 30 minutos."})
        if inicio.minute not in (0, 30) or inicio.second or inicio.microsecond:
            raise ValidationError({"inicio": "O horário deve iniciar em um bloco de 30 minutos."})
        if inicio.hour < 7 or fim.time().hour > 23:
            raise ValidationError({"inicio": "O horário deve estar entre 07:00 e 23:00."})

    def __str__(self):
        return f"{self.inicio:%H:%M}-{self.fim:%H:%M} ({self.data:%d/%m/%Y})"
