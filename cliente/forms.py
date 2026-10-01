from django import forms

from .models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ("nome", "cpf", "telefone")
        labels = {
            "nome": "Nome",
            "cpf": "CPF (somente números)",
            "telefone": "Telefone (somente números)",
        }
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "cpf": forms.TextInput(
                attrs={"class": "form-control", "inputmode": "numeric", "maxlength": "11"}
            ),
            "telefone": forms.TextInput(
                attrs={"class": "form-control", "inputmode": "numeric", "maxlength": "11"}
            ),
        }
