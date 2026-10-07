from decimal import Decimal, InvalidOperation

from django import forms

from catalogo.models import Produto, Servico 
from configuracao.models import DadosEstabelecimento

from .models import PagamentoVenda

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
            raise forms.ValidationError(
                "Informe um valor monetário válido."
            ) from exc

class FinalizarVendaForm(forms.Form):

    MAX_PAGAMENTOS_ADICIONAIS = 6

    forma_pagamento = forms.ChoiceField(
        choices=PagamentoVenda.FormaPagamento.choices,
        label="Forma de pagamento",
        widget=forms.Select(
            attrs={
                "class": "form-select", 
                "id": "forma-pagamento"
            }
        ),
    )

    valor_recebido = ValorMoedaField(
        required=False,
        label="Valor do pagamento principal",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "inputmode": "decimal",
                "placeholder": "R$ 0,00",
                "id": "valor-recebido",
            }
        ),
    )

    quantidade_pagamentos_adicionais = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=MAX_PAGAMENTOS_ADICIONAIS,
        initial=0,
        label="Quantidade de pagamentos adicionais",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": 0,
                "max": MAX_PAGAMENTOS_ADICIONAIS,
                "placeholder": "0",
                "id": "quantidade-pagamentos-adicionais",
            }
        ),
    )

    pagamento_multiplo = forms.BooleanField(
        required=False,
        label="Múltiplos Pagamentos",
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "id": "id_pagamento_multiplo",
            }
        ),
    )

    nome_cliente = forms.CharField(
        required=False,
        max_length=120,
        label="Nome do cliente",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "autocomplete": "name",
                "placeholder": "Nome do cliente",
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
        self.total = Decimal(total or '0.00')

        super().__init__(*args, **kwargs)

        self.quantidade_pagamentos_adicionais = self.obter_quantidade_pagamentos_adicionais()
        self.configurar_pagamentos_adicionais()

    # PAGAMENTO ADICIONAIS ===============================================================
    def obter_quantidade_pagamentos_adicionais(self):
        quantidade = 0

        if self.is_bound:
            valor = self.data.get("quantidade_pagamentos_adicionais")

            if valor not in (None, ""):
                try:
                    quantidade = int(valor)
                except (TypeError, ValueError):
                    quantidade = 0

            indices_presentes = []

            for chave in self.data:

                if chave.startswith("forma_pagamento_") or chave.startswith("valor_pagamento_"):
                    partes = chave.split("_")

                    if len(partes) >= 3 and partes[-1].isdigit():
                        indices_presentes.append(int(partes[-1]))

            if indices_presentes:
                quantidade = max(quantidade, max(indices_presentes) - 1)

        else:
            valor = self.initial.get("quantidade_pagamentos_adicionais")

            if valor is None:
                valor = self.fields["quantidade_pagamentos_adicionais"].initial

            if valor not in (None, ""):
                try:
                    quantidade = int(valor)
                except (TypeError, ValueError):
                    quantidade = 0

        return max(0, min(quantidade, self.MAX_PAGAMENTOS_ADICIONAIS))

    def configurar_pagamentos_adicionais(self):
        for nome in list(self.fields):

            if nome.startswith("forma_pagamento_") and nome != "forma_pagamento":
                del self.fields[nome]

            elif nome.startswith("valor_pagamento_"):
                del self.fields[nome]

        for indice in range(2, self.quantidade_pagamentos_adicionais + 2):

            self.fields[f"forma_pagamento_{indice}"] = forms.ChoiceField(
                choices=PagamentoVenda.FormaPagamento.choices,
                required=False,
                label=f"Pagamento {indice}",
                widget=forms.Select(
                    attrs={
                        "class": "form-select"
                    }
                ),
            )

            self.fields[f"valor_pagamento_{indice}"] = ValorMoedaField(
                required=False,
                label=f"Valor do pagamento {indice}",
                widget=forms.TextInput(
                    attrs={
                        "class": "form-control",
                        "inputmode": "decimal",
                        "placeholder": "R$ 0,00",
                    }
                ),
            )

        self.pagamentos_adicionais = [
            {
                "indice": indice,
                "forma": self[f"forma_pagamento_{indice}"],
                "valor": self[f"valor_pagamento_{indice}"],
            }
            for indice in range(2, self.quantidade_pagamentos_adicionais + 2)
        ]

    def pagamentos_adicionais_indices(self):
        quantidade = self.cleaned_data.get(
            "quantidade_pagamentos_adicionais",
            self.quantidade_pagamentos_adicionais,
        )

        indices = []

        for chave in self.data:

            if chave.startswith("forma_pagamento_") or chave.startswith("valor_pagamento_"):
                partes = chave.split("_")

                if len(partes) >= 3 and partes[-1].isdigit():
                    indices.append(int(partes[-1]))

        if indices:
            return range(2, max(indices) + 1)
        
        return range(2, (quantidade or 0) + 2)

    # CONSTRUÇÃO DOS PAGAMENTOS =============================================================
    def pagamentos(self):
        pagamentos = []

        forma_principal = self.cleaned_data.get("forma_pagamento")
        valor_principal = self.cleaned_data.get("valor_recebido")

        # Pagamentos adicionais
        pagamentos_adicionais = []

        for indice in self._pagamentos_adicionais_indices():

            forma_pagamento = self.cleaned_data.get(f"forma_pagamento_{indice}")
            valor_pagamento = self.cleaned_data.get(f"valor_pagamento_{indice}")

            if forma_pagamento and valor_pagamento is not None:
                pagamentos_adicionais.append(
                    {
                        'forma_pagamento': forma_pagamento,
                        'valor_pagamento': valor_pagamento
                    }
                )

        # Soma dos pagamentos adicionais
        total_adicionais = sum(
            (
                pagamento['valor']
                for pagamento in pagamentos_adicionais
            ),
            Decimal('0.00')
        )

        # Nenhuma forma de pagamento
        if not forma_principal:
            return []

        # PAGAMENTO ÚNICO
        if not self.cleaned_data.get(
            'pagamento_multiplo',
            False
        ):
            if (
                forma_principal == PagamentoVenda.FormaPagamento.DINHEIRO
            ):
                if valor_principal is None:
                    return []

                valor = self.total

                troco = max(
                    valor_principal - valor,
                    Decimal('0.00')
                )

                pagamentos.append(
                    {
                        'forma_pagamento': forma_principal,
                        'valor_pagamento': valor_pagamento,
                        'valor_recebido': valor_principal,
                        'troco': troco
                    }
                )

            else:
                pagamentos.append(
                    {
                        'forma_pagamento': forma_principal,
                        'valor_pagamento': self.total,
                        'valor_recebido': self.total,
                        'troco': Decimal('0.00')
                    }
                )

            return pagamentos

        # PAGAMENTO DIVIDIDO
        restante = self.total - total_adicionais

        if restante <= 0:
            return []

        # Principal em dinheiro
        if (
            forma_principal == PagamentoVenda.FormaPagamento.DINHEIRO
        ):
            if self.valor_principal is None:
                return []

            valor_principal_pagamento = restante

            troco = max(
                valor_principal - valor_principal_pagamento,
                Decimal('0.00')
            )

            pagamentos.append(
                {
                    'forma_pagamento': forma_principal,
                    'valor_pagamento': valor_principal_pagamento,
                    'valor_recebido': valor_principal,
                    'troco': troco
                }
            )

        # Principal não monetário
        else:
            pagamentos.append(
                {
                    'forma_pagamento': forma_principal,
                    'valor_pagamento': restante,
                    'valor_recebido': restante,
                    'troco': Decimal('0.00')  
                }
            )

        # Adicionais
        for pagamento in pagamentos_adicionais:
            pagamentos.append(
                {
                    'forma_pagamento': pagamento['forma_pagamento'],
                    'valor_pagamento': pagamento['valor_pagamento'],
                    'valor_recebido': pagamento['valor_pagamento'],
                    'troco': Decimal('0.00')
                }
            )

        return pagamentos

    # VALIDAÇÕES ========================================================================
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

        forma_principal = cleaned_data.get("forma_pagamento")
        valor_principal = cleaned_data.get("valor_recebido")
        pagamento_multiplo = cleaned_data.get("pagamento_multiplo", False)

        pagamentos_adicionais = []

        for indice in self.pagamentos_adicionais_indices():

            forma_pagamento = cleaned_data.get(f"forma_pagamento_{indice}")
            valor_pagamento = cleaned_data.get(f"valor_pagamento_{indice}")

            # Forma sem valor
            if forma_pagamento and valor_pagamento is None:
                    self.add_error(
                        f"valor_pagamento_{indice}",
                        "Informe o valor desse pagamento.",
                    )
                    continue

            # Valor sem forma
            if valor_pagamento is not None and not forma_pagamento:
                    self.add_error(
                        f'valor_pagamento_{indice}',
                        'Informe o valor desse pagamento.'
                    )
                    continue

            if forma_pagamento and valor_pagamento is not None:
                if valor_pagamento <= 0:
                    self.add_error(
                        f'valor_pagamento_{indice}',
                        'O valor do pagamento deve ser maior que zero.'
                    )

                pagamentos_adicionais.append(
                    {
                        'forma_pagamento': forma_pagamento,
                        'valor_pagamento': valor_pagamento
                    }
                )

        total_adicionais = sum(
            (
                pagamento['valor']
                for pagamento in pagamentos_adicionais
            ),
            Decimal('0.00')
        )

        # PAGAMENTO ÚNICO
        if not pagamento_multiplo:

            if pagamentos_adicionais:
                self.add_error(
                    'pagamento_multiplo',
                    'Ative a opção de múltiplos pagamentos para informar pagamentos adicionais.'
                )

            if (
                forma_principal == PagamentoVenda.FormaPagamento.DINHEIRO
            ):
                if valor_principal is None:
                    self.add_error(
                        'valor_recebido',
                        'Informe quanto foi recebido para calcular o troco.'
                    )

                elif valor_principal < self.total:
                    self.add_error(
                        'valor_recebido',
                        'O valor recebido deve ser igual ou maior que o total da venda.'
                    )
            
            elif forma_principal:
                # Para cartão/pix o valor da venda é quitado integralmente pelo pagamento
                pass
                
            return cleaned_data

        # PAGAMENTO DIVIDIDO
        

class DadosEstabelecimentoForm(forms.ModelForm):
    class Meta:
        model = DadosEstabelecimento
        fields = ("nome", "horario_funcionamento", "endereco", "limite_gastos")
        labels = {
            "nome": "Nome do estabelecimento",
            "horario_funcionamento": "Horário de funcionamento",
            "endereco": "Endereço do estabelecimento",
            "limite_gastos": "Margem máxima de gastos (R$)",
        }
        widgets = {
            "nome": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nome do estabelecimento",
                    "autocomplete": "organization",
                }
            ),
            "horario_funcionamento": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex.: Seg. a sex., das 9h às 18h",
                }
            ),
            "endereco": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Rua, número, bairro e cidade",
                    "autocomplete": "street-address",
                }
            ),
            "limite_gastos": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                    "placeholder": "Ex.: 5000,00",
                }
            ),
        }


class FiltroVendasForm(forms.Form):
    pagamentos = forms.MultipleChoiceField(
        required=False,
        choices=Venda.FormaPagamento.choices,
        label="Pagamento",
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-select",
                "size": 1,
                "style": "height: 38px",
            }
        ),
    )
    data_inicial = forms.DateField(
        required=False,
        label="Data inicial",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    data_final = forms.DateField(
        required=False,
        label="Data final",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        data_inicial = cleaned_data.get("data_inicial")
        data_final = cleaned_data.get("data_final")
        if data_inicial and data_final and data_inicial > data_final:
            self.add_error(
                "data_final",
                "A data final deve ser igual ou posterior à data inicial.",
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
                "nome_cliente": venda.nome_cliente,
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
