from datetime import date, datetime, time, timedelta

from django import forms

from .models import Agendamento, HorarioAgendado


def horarios_disponiveis():
    horarios = []
    inicio = datetime.combine(date.today(), time(7, 0))
    fim_expediente = datetime.combine(date.today(), time(23, 0))
    while inicio < fim_expediente:
        fim = inicio + timedelta(minutes=30)
        horarios.append((inicio.strftime("%H:%M"), f"{inicio:%H:%M}–{fim:%H:%M}"))
        inicio = fim
    return horarios


class AgendamentoForm(forms.ModelForm):
    data = forms.DateField(widget=forms.HiddenInput, label="Data")
    horarios = forms.MultipleChoiceField(
        choices=horarios_disponiveis,
        required=True,
        label="Horários",
        error_messages={"required": "Selecione pelo menos um bloco de horário."},
    )
    servicos = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Serviços (opcional)",
    )

    class Meta:
        model = Agendamento
        fields = ("data", "nome", "telefone", "email", "servicos")
        labels = {
            "nome": "Nome",
            "telefone": "Telefone (WhatsApp)",
            "email": "E-mail (opcional)",
        }
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control", "autocomplete": "name"}),
            "telefone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "type": "tel",
                    "autocomplete": "tel",
                    "placeholder": "(00) 00000-0000",
                }
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "autocomplete": "email"}
            ),
        }

    def __init__(self, *args, selected_date=None, **kwargs):
        super().__init__(*args, **kwargs)
        from servico.models import Servico

        self.fields["servicos"].queryset = Servico.objects.order_by("descricao")
        if selected_date is not None:
            self.initial["data"] = selected_date
        if self.instance.pk:
            self.initial["horarios"] = list(
                self.instance.horarios.values_list("inicio", flat=True)
            )
            self.initial["horarios"] = [
                horario.strftime("%H:%M") for horario in self.initial["horarios"]
            ]

    def clean_horarios(self):
        horarios = self.cleaned_data["horarios"]
        data = self.cleaned_data.get("data")
        if data is None:
            return horarios

        consulta = HorarioAgendado.objects.filter(data=data, inicio__in=horarios)
        if self.instance.pk:
            consulta = consulta.exclude(agendamento=self.instance)
        if consulta.exists():
            raise forms.ValidationError(
                "Um ou mais blocos foram reservados por outra pessoa. "
                "Escolha novamente entre os horários disponíveis."
            )
        return horarios

    def clean_telefone(self):
        telefone = self.cleaned_data["telefone"].strip()
        if not telefone:
            raise forms.ValidationError("Informe o telefone/WhatsApp.")
        return telefone
