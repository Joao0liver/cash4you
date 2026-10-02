from django import forms

from .models import ContaPagar


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
