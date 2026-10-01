from django import forms

from core.pricing import calculate_markup_price

from .models import Servico


class ServicoForm(forms.ModelForm):
    despesas_variaveis_percentual = forms.DecimalField(
        label="Despesas variáveis (%)",
        help_text="Impostos, taxas, comissões e outros custos percentuais cobrados sobre a venda.",
        min_value=0,
        max_value=100,
        decimal_places=2,
        max_digits=5,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "min": "0", "max": "100", "step": "0.01"}
        ),
    )
    lucro_desejado_percentual = forms.DecimalField(
        label="Lucro desejado (%)",
        help_text="Percentual de lucro líquido desejado sobre o preço final.",
        min_value=0,
        max_value=100,
        decimal_places=2,
        max_digits=5,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "min": "0", "max": "100", "step": "0.01"}
        ),
    )
    preco_venda = forms.DecimalField(
        label="Preço de venda",
        help_text="Sugestão calculada pelo markup. Você pode ajustar este valor antes de salvar.",
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "min": "0", "step": "0.01"}
        ),
    )

    class Meta:
        model = Servico
        fields = (
            "descricao",
            "custo_direto",
            "despesas_variaveis_percentual",
            "lucro_desejado_percentual",
            "preco_venda",
        )
        labels = {
            "descricao": "Descrição",
            "custo_direto": "Custo variável direto por atendimento",
        }
        help_texts = {
            "descricao": "Nome que identifica o serviço.",
            "custo_direto": "Valor dos materiais e demais custos diretos de realizar um atendimento.",
        }
        widgets = {
            "descricao": forms.TextInput(
                attrs={"class": "form-control", "title": "Nome que identifica o serviço."}
            ),
            "custo_direto": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                    "title": "Valor dos materiais e demais custos diretos de realizar um atendimento.",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["despesas_variaveis_percentual"].widget.attrs["title"] = (
            self.fields["despesas_variaveis_percentual"].help_text
        )
        self.fields["lucro_desejado_percentual"].widget.attrs["title"] = (
            self.fields["lucro_desejado_percentual"].help_text
        )
        self.fields["preco_venda"].widget.attrs["title"] = self.fields[
            "preco_venda"
        ].help_text

    def clean(self):
        cleaned_data = super().clean()
        direct_cost = cleaned_data.get("custo_direto")
        expenses = cleaned_data.get("despesas_variaveis_percentual")
        profit = cleaned_data.get("lucro_desejado_percentual")

        if direct_cost is None or expenses is None or profit is None:
            return cleaned_data

        if expenses + profit >= 100:
            self.add_error(
                "lucro_desejado_percentual",
                "A soma das despesas variáveis e do lucro deve ser menor que 100%.",
            )
            return cleaned_data

        if cleaned_data.get("preco_venda") is None:
            cleaned_data["preco_venda"] = calculate_markup_price(
                direct_cost,
                expenses,
                profit,
            )
        return cleaned_data
