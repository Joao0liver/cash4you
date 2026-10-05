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

            'preco_venda': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),

            'preco_custo': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),

            'quantidade': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Somente números',
                'min': '0'
            }),
        }

    def clean_descricao(self):
        descricao = self.cleaned_data['descricao'].strip()

        if not descricao:
            raise forms.ValidationError(
                'O nome do produto é obrigatório.'
            )
        
        return descricao

    def clean_preco_venda(self):
        preco_venda = self.cleaned_data['preco_venda']

        if preco_venda <= 0:
            raise forms.ValidationError(
                'O preço de venda deve ser maior que 0.'
            )

        return preco_venda

    def clean_preco_custo(self):
        preco_custo = self.cleaned_data['preco_custo']

        if preco_custo <= 0:
            raise forms.ValidationError(
                'O preço de custo deve ser maior que 0.'
            )

        return preco_custo

    def clean_quantidade(self):
        quantidade = self.cleaned_data['quantidade']

        if quantidade < 0:
            raise forms.ValidationError(
                'A quantidade não pode ser negativa.'
            )

        return quantidade

    def clean(self):
        cleaned_data = super().clean()

        preco_venda = cleaned_data.get('preco_venda')
        preco_custo = cleaned_data.get('preco_custo')

        if preco_venda is not None and preco_custo is not None:

            if preco_venda < preco_custo:
                raise forms.ValidationError(
                    'O preço de venda não pode ser menor que o preço de custo.'
                )

        return cleaned_data

class ServicoForm(forms.ModelForm):

    class Meta:
        model = Servico
        fields = ['descricao', 'preco_venda']

        widgets = {
            'descricao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do produto'
            }),

            'preco_venda': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
        }

    def clean_descricao(self):
        descricao = self.cleaned_data['descricao'].strip()

        if not descricao:
            raise forms.ValidationError(
                'O nome do serviço é obrigatório.'
            )
        
        return descricao

    def clean_preco_venda(self):
        preco_venda = self.cleaned_data['preco_venda']

        if preco_venda <= 0:
            raise forms.ValidationError(
                'O preço de venda deve ser maior que 0.'
            )

        return preco_venda
