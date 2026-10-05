from django import forms
from django.db.models import Sum

from venda.models import DadosEstabelecimento
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
                format="%Y-%m-%d",
                attrs={"class": "form-control", "type": "date"},
            ),
            "paga": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        valor = cleaned_data.get("valor")
        paga = cleaned_data.get("paga", False)
        if valor is None or paga:
            return cleaned_data

        configuracao = DadosEstabelecimento.objects.filter(pk=1).first()
        limite = configuracao.limite_gastos if configuracao else None
        if limite is None:
            return cleaned_data

        pendentes = ContaPagar.objects.filter(paga=False)
        if self.instance.pk:
            pendentes = pendentes.exclude(pk=self.instance.pk)
        total_pendente = pendentes.aggregate(total=Sum("valor"))["total"] or 0
        if total_pendente + valor > limite:
            self.add_error(
                "valor",
                f"Este valor ultrapassa a margem máxima de gastos de R$ {limite:.2f}. "
                f"Contas pendentes somam R$ {total_pendente:.2f}.",
            )
        return cleaned_data


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
