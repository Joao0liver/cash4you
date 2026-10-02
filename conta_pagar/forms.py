from django import forms

from .models import ContaPagar, Funcionario


class ContaPagarForm(forms.ModelForm):
    class Meta:
        model = ContaPagar
        fields = ("descricao", "valor", "vencimento", "paga")
        labels = {
            "descricao": "Descrição",
            "valor": "Valor",
            "vencimento": "Data de vencimento",
            "paga": "Conta paga",
        }
        widgets = {
            "descricao": forms.TextInput(
                attrs={"class": "form-control", "autocomplete": "off"}
            ),
            "valor": forms.NumberInput(
                attrs={"class": "form-control", "min": "0", "step": "0.01"}
            ),
            "vencimento": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "paga": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = ("nome", "funcao")
        labels = {
            "nome": "Nome",
            "funcao": "Função na empresa",
        }
        widgets = {
            "nome": forms.TextInput(
                attrs={"class": "form-control", "autocomplete": "name"}
            ),
            "funcao": forms.TextInput(
                attrs={"class": "form-control", "autocomplete": "organization-title"}
            ),
        }
