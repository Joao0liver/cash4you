from django import forms
from .models import Cliente

class ClienteForm(forms.ModelForm):

    class Meta:
        model = Cliente
        fields = ['nome', 'cpf', 'telefone']

        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo'
            }),

            'cpf': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Somente números',
                'maxlength': '11'
            }),

            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Somente números',
                'maxlength': '11'
            }),
        }