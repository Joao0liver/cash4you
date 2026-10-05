from django import forms
from .models import Cliente
import re

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

    def clean_cpf(self):
        cpf = self.cleaned_data['cpf']

        # Remove pontos, traços, espaços e qualquer outro caractere
        cpf = re.sub(r'\D', '', cpf)

        if len(cpf) != 11:
            raise forms.ValidationError(
                'O CPF deve possuir 11 dígitos.'
            )

        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            raise forms.ValidationError(
                'Informe um CPF válido.'
            )

        # Cálculo do segundo dígito verificador
        soma = sum(
            int(cpf[i]) * (11 - i)
            for i in range(10)
        )

        resto = soma % 11
        segundo_digito = 0 if resto < 2 else 11 - resto

        if segundo_digito != int(cpf[10]):
            raise forms.ValidationError(
                'Informe um CPF válido.'
            )

        return cpf