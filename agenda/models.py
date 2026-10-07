from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.db import models
import re

class Agendamento(models.Model):

    data = models.DateField()
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    funcionario = models.ForeignKey(
        'usuario.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agendamentos',
    )
    descricao_agendar_para = models.CharField(max_length=160, blank=True)
    servicos = models.ManyToManyField(
        'catalogo.Servico',
        blank=True,
        related_name='agendamentos',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('data', 'nome', 'id')

    @property
    def whatsapp_numero(self):
        numero = re.sub(r'\D', '', self.telefone)
        if len(numero) in (10, 11):
            return f'55{numero}'
        return numero

    @property
    def agendar_para_display(self):
        if self.funcionario_id:
            return self.funcionario.nome
        return self.descricao_agendar_para or '—'

    def __str__(self):
        return f'{self.nome} - {self.data:%d/%m/%Y}'


class HorarioAgendado(models.Model):

    agendamento = models.ForeignKey(
        Agendamento,
        on_delete=models.CASCADE,
        related_name='horarios',
    )
    inicio = models.TimeField()
    fim = models.TimeField()

    class Meta:
        ordering = ('inicio',)

    def clean(self):
        super().clean()

        # Se não existir um agendamento
        if not self.agendamento_id:
            return

        # Se o usuário não for do Group Funcionário
        if self.funcionario_id:
            if not self.funcionario.groups.filter(name='Funcionário').exists():
                raise ValidationError({
                    'funcionario':
                        'O usuário selecionado não pertence ao grupo Funcionário.'
                })

        inicio = datetime.combine(self.agendamento.data, self.inicio)
        fim = datetime.combine(self.agendamento.data, self.fim)

        # O bloco deve ter exatamente 30 minutos
        if fim - inicio != timedelta(minutes=30):
            raise ValidationError({
                'fim': 'O bloco deve ter exatamente 30 minutos.'
            })

        # O início deve ser 00 ou 30 minutos
        if inicio.minute not in (0, 30) or inicio.second or inicio.microsecond:
            raise ValidationError({
                'inicio': 'O horário deve iniciar em um bloco de 30 minutos.'
            })

        # Só são permitidos horários entre as 07:00 e as 23:00
        if inicio.hour < 7 or fim.time().hour > 23:
            raise ValidationError({
                'inicio': 'O horário deve estar entre 07:00 e 23:00.'
            })

        # Verifica conflito de agenda
        conflito = HorarioAgendado.objects.filter(
            agendamento__data = self.agendamento.data,
            inicio = self.inicio,
        ).exclude(id=self.id)

        if self.agendamento.funcionario_id:
            conflito = conflito.filter(
                agendamento__funcionario_id = self.agendamento.funcionario_id
            )
        else:
            descricao = self.agendamento.descricao_agendar_para.strip()
            conflito = conflito.filter(
                agendamento__funcionario__isnull = True,
                agendamento__descricao_agendar_para = descricao,
            )

        if conflito.exists():
            raise ValidationError({
                'inicio': 'Este recurso já possui um agendamento nesse horário.'
            })

    def __str__(self):
        return f"{self.inicio:%H:%M}-{self.fim:%H:%M} ({self.agendamento.data:%d/%m/%Y})"
