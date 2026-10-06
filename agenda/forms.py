from datetime import date, datetime, time, timedelta
from django import forms
from .models import Agendamento, HorarioAgendado
from usuario.models import Usuario

def horarios_disponiveis():
    horarios = []

    inicio = datetime.combine(date.today(), time(7, 0))
    fim_expediente = datetime.combine(date.today(), time(23, 0))

    while inicio < fim_expediente:
        fim = inicio + timedelta(minutes=30)

        horarios.append(
            (inicio.strftime("%H:%M"), f"{inicio:%H:%M}-{fim:%H:%M}")
        )
        inicio = fim

    return horarios

class AgendamentoForm(forms.ModelForm):

    data = forms.DateField(widget=forms.HiddenInput, label="Data")
    tipo_agendar_para = forms.ChoiceField(
        choices=(
            ("funcionario", "Funcionário"),
            ("manual", "Descrição manual"),
        ),
        required=False,
        initial="manual",
        widget=forms.RadioSelect,
        label="Agendar para",
    )
    funcionario = forms.ModelChoiceField(
        queryset=Usuario.objects.none(),
        required=False,
        empty_label="Selecione um funcionário",
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Funcionário",
    )
    descricao_agendar_para = forms.CharField(
        required=False,
        max_length=160,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "off",
                "placeholder": "Ex.: atendimento geral",
            }
        ),
        label="Descrição",
    )
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
        fields = (
            "data",
            "nome",
            "telefone",
            "email",
            "funcionario",
            "descricao_agendar_para",
            "servicos",
        )

        labels = {
            "nome": "Nome do Cliente",
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

        from catalogo.models import Servico

        # Somente usuários pertencentes ao grupo Funcionário
        self.fields['funcionario'].queryset = Usuario.objects.filter(
            groups__name = 'Funcionário'
        ).order_by('nome')

        #Serviços disponíveis
        self.fields["servicos"].queryset = Servico.objects.order_by("descricao")

        # Define o tipo de agendamento na edição
        if self.instance.id:

            if self.instance.funcionario_id:
                self.initial["tipo_agendar_para"] = "funcionario"

            elif self.instance.descricao_agendar_para:
                self.initial["tipo_agendar_para"] = "manual"

            else:
                self.initial["tipo_agendar_para"] = ""

        # Define a data selecionada
        if selected_date is not None:
            self.initial["data"] = selected_date

        # Carrega os horários indisponíveis na edição
        if self.instance.id:
            self.initial["horarios"] = list(
                self.instance.horarios.values_list("inicio", flat=True)
            )
            self.initial["horarios"] = [
                horario.strftime("%H:%M") for horario in self.initial["horarios"]
            ]

    def clean(self):
        cleaned_data = super().clean()

        tipo = cleaned_data.get("tipo_agendar_para")
        funcionario = cleaned_data.get("funcionario")
        descricao = cleaned_data.get("descricao_agendar_para", "").strip()

        # Nenhum tipo de agendamento
        if not tipo:
            if not (
                self.instance.id
                and not self.instance.funcionario_id
                and not self.instance.descricao_agendar_para
                and not funcionario
                and not descricao
            ):
                self.add_error(
                    "tipo_agendar_para",
                    "Escolha um funcionário ou uma descrição manual.",
                )

        # Agendamento do tipo funcionário
        elif tipo == "funcionario":
            if not funcionario:
                self.add_error(
                    "funcionario", 
                    "Selecione um funcionário."
                )
            cleaned_data["descricao_agendar_para"] = ""

        # Agendamento do tipo descrição (manual)
        elif tipo == "manual":
            if not descricao:
                self.add_error(
                    "descricao_agendar_para",
                    "Informe a descrição de para quem é o agendamento.",
                )
            cleaned_data["funcionario"] = None
            cleaned_data['descricao_agendar_para'] = descricao

        return cleaned_data

    def save(self, commit=True):
        agendamento = super().save(commit=False)

        agendamento.funcionario = self.cleaned_data.get("funcionario")
        agendamento.descricao_agendar_para = self.cleaned_data.get("descricao_agendar_para", "")

        if commit:
            agendamento.save()
            self.save_m2m()

        return agendamento

    def clean_horarios(self):
        horarios = self.cleaned_data["horarios"]
        data = self.cleaned_data.get("data")

        if data is None:
            return horarios

        tipo = self.cleaned_data.get('tipo_agendar_para')
        funcionario = self.cleaned_data.get('funcionario')
        descricao = self.cleaned_data.get('descricao_agendar_para', '').strip()

        # Começa procurando os horários da data selecionada
        consulta = HorarioAgendado.objects.filter(
            agendamento__data = data,
            inicio__in = horarios,
        )

        # Filtra pelo funcionario
        if tipo == 'funcionario' and funcionario:
            consulta = consulta.filter(
                agendamento__funcionario_id = funcionario.id
            )

        # Filtra pela descrição (manual)
        elif tipo == 'manual' and descricao:
            consulta = consulta.filter(
                agendamento__funcionario__isnull = True,
                agendamento__descricao_agendar_para = descricao
            )

        # Nenhum tipo definido - não há agenda específica para verificar
        else:
            return horarios

        # Ignora os horários do próprio agendamento na edição dos dados
        if self.instance.id:
            consulta = consulta.exclude(
                agendamento = self.instance
            )

        if consulta.exists():
            raise forms.ValidationError(
                "Um ou mais blocos já foram reservados nesta agenda. "
                "Escolha novamente entre os horários disponíveis."
            )
        
        return horarios

    def clean_telefone(self):
        telefone = self.cleaned_data["telefone"].strip()

        if not telefone:
            raise forms.ValidationError(
                "Informe o telefone/WhatsApp."
            )
        
        return telefone
