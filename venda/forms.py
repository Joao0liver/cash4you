from decimal import Decimal, InvalidOperation

from django import forms

from produto.models import Produto
from servico.models import Servico

from .models import Venda


class ValorMoedaField(forms.CharField):
    def to_python(self, value):
        value = super().to_python(value)
        if not value:
            return None

        valor = value.replace("R$", "").replace(" ", "").strip()
        if "," in valor:
            valor = valor.replace(".", "").replace(",", ".")
        try:
            return Decimal(valor)
        except InvalidOperation as exc:
            raise forms.ValidationError("Informe um valor monetário válido.") from exc


class FinalizarVendaForm(forms.Form):
    forma_pagamento = forms.ChoiceField(
        choices=Venda.FormaPagamento.choices,
        label="Forma de pagamento",
        widget=forms.Select(attrs={"class": "form-select", "id": "forma-pagamento"}),
    )
    valor_recebido = ValorMoedaField(
        required=False,
        label="Valor recebido em dinheiro",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "inputmode": "decimal",
                "placeholder": "R$ 0,00",
                "id": "valor-recebido",
            }
        ),
    )
    telefone_whatsapp = forms.CharField(
        required=False,
        label="Telefone do cliente para WhatsApp (opcional)",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "type": "tel",
                "autocomplete": "tel",
                "placeholder": "(00) 00000-0000",
            }
        ),
    )

    def __init__(self, *args, total, **kwargs):
        self.total = total
        super().__init__(*args, **kwargs)

    def clean_valor_recebido(self):
        valor_recebido = self.cleaned_data["valor_recebido"]
        if valor_recebido is not None and valor_recebido < 0:
            raise forms.ValidationError("O valor recebido não pode ser negativo.")
        return valor_recebido

    def clean_telefone_whatsapp(self):
        telefone = self.cleaned_data["telefone_whatsapp"]
        digitos = "".join(caractere for caractere in telefone if caractere.isdigit())
        if not digitos:
            return ""
        if digitos.startswith("55") and len(digitos) in (12, 13):
            digitos = digitos[2:]
        if len(digitos) not in (10, 11):
            raise forms.ValidationError(
                "Informe um telefone com DDD e 10 ou 11 dígitos para o WhatsApp."
            )
        return digitos

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("forma_pagamento") == Venda.FormaPagamento.DINHEIRO:
            recebido = cleaned_data.get("valor_recebido")
            if recebido is None:
                self.add_error(
                    "valor_recebido",
                    "Informe quanto foi recebido para calcular o troco.",
                )
            elif recebido < self.total:
                self.add_error(
                    "valor_recebido",
                    "O valor recebido deve ser igual ou maior que o total da venda.",
                )
        return cleaned_data


class EditarVendaForm(FinalizarVendaForm):
    def __init__(self, *args, venda, **kwargs):
        self.venda = venda
        self.produtos = list(Produto.objects.order_by("descricao"))
        self.servicos = list(Servico.objects.order_by("descricao"))
        self.produtos_vendidos = {}
        self.servicos_vendidos = {}
        for item in venda.itens.all():
            if item.produto_id:
                self.produtos_vendidos[item.produto_id] = (
                    self.produtos_vendidos.get(item.produto_id, 0) + item.quantidade
                )
            elif item.servico_id:
                self.servicos_vendidos[item.servico_id] = (
                    self.servicos_vendidos.get(item.servico_id, 0) + item.quantidade
                )

        kwargs.setdefault(
            "initial",
            {
                "forma_pagamento": venda.forma_pagamento,
                "valor_recebido": venda.valor_recebido,
                "telefone_whatsapp": venda.telefone_whatsapp,
            },
        )
        super().__init__(*args, total=Decimal("0.00"), **kwargs)

        self.produto_campos = []
        self.servico_campos = []
        for produto in self.produtos:
            nome = f"produto_{produto.pk}"
            self.fields[nome] = forms.IntegerField(
                label=produto.descricao,
                min_value=0,
                required=False,
                initial=self.produtos_vendidos.get(produto.pk, 0),
                widget=forms.NumberInput(
                    attrs={
                        "class": "form-control",
                        "min": "0",
                        "max": produto.quantidade + self.produtos_vendidos.get(produto.pk, 0),
                    }
                ),
            )
            self.produto_campos.append(
                {
                    "nome": nome,
                    "item": produto,
                    "estoque_disponivel": (
                        produto.quantidade + self.produtos_vendidos.get(produto.pk, 0)
                    ),
                }
            )
        for servico in self.servicos:
            nome = f"servico_{servico.pk}"
            self.fields[nome] = forms.IntegerField(
                label=servico.descricao,
                min_value=0,
                required=False,
                initial=self.servicos_vendidos.get(servico.pk, 0),
                widget=forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            )
            self.servico_campos.append({"nome": nome, "item": servico})

    def clean(self):
        cleaned_data = super(FinalizarVendaForm, self).clean()
        total = Decimal("0.00")
        quantidade_total = 0
        for campo in self.produto_campos:
            quantidade = cleaned_data.get(campo["nome"]) or 0
            quantidade_total += quantidade
            if quantidade > campo["estoque_disponivel"]:
                self.add_error(
                    campo["nome"],
                    f"Estoque disponível para esta edição: {campo['estoque_disponivel']}.",
                )
            total += campo["item"].preco_venda * quantidade
        for campo in self.servico_campos:
            quantidade = cleaned_data.get(campo["nome"]) or 0
            quantidade_total += quantidade
            total += campo["item"].preco_venda * quantidade

        if quantidade_total == 0:
            self.add_error(None, "A venda deve conter pelo menos um item.")
        self.total = total
        return FinalizarVendaForm.clean(self)

    def itens_selecionados(self):
        itens = []
        for campo in self.produto_campos:
            quantidade = self.cleaned_data.get(campo["nome"]) or 0
            if quantidade:
                itens.append(("produto", campo["item"], quantidade))
        for campo in self.servico_campos:
            quantidade = self.cleaned_data.get(campo["nome"]) or 0
            if quantidade:
                itens.append(("servico", campo["item"], quantidade))
        return itens
