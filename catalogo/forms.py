from django import forms
from .models import Produto, Servico

class ProdutoForm(forms.ModelForm):

    class Meta:
        model = Produto
        fields = ['descricao', 'preco_venda', 'preco_custo', 'quantidade']

        widgets = {
            'descricao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do produto'
            }),

            'preco_venda': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Somente números',
                'maxlength': '10'
            }),

            'preco_custo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Somente números',
                'maxlength': '10'
            }),

            'quantidade': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Somente números',
                'maxlength': '10'
            }),
        }
