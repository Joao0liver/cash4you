from django import forms

from .models import DadosEstabelecimento

class DadosEstabelecimentoForm(forms.ModelForm):

    class Meta:
        model = DadosEstabelecimento
        
        fields = ("nome", "horario_funcionamento", "endereco", "limite_gastos")
        labels = {
            "nome": "Nome do estabelecimento",
            "horario_funcionamento": "Horário de funcionamento",
            "endereco": "Endereço do estabelecimento",
            "limite_gastos": "Margem máxima de gastos (R$)",
        }
        widgets = {
            "nome": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nome do estabelecimento",
                    "autocomplete": "organization",
                }
            ),
            "horario_funcionamento": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex.: Seg. a sex., das 9h às 18h",
                }
            ),
            "endereco": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Rua, número, bairro e cidade",
                    "autocomplete": "street-address",
                }
            ),
            "limite_gastos": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                    "placeholder": "Ex.: 5000,00",
                }
            ),
        }