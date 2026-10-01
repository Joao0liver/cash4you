from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone
from django import forms

from produto.models import Produto
from venda.models import ItemVenda, Venda


def cadastros(request):
    return render(request, "cadastros.html")


def precificar(request):
    return render(request, "precificar.html")


def _periodos_comparacao(tipo, hoje):
    if tipo == "semanas":
        inicio_atual = hoje - timedelta(days=hoje.weekday())
        intervalos = []
        for recuo in (2, 1, 0):
            inicio = inicio_atual - timedelta(weeks=recuo)
            fim = inicio + timedelta(weeks=1)
            intervalos.append((inicio, fim, f"Semana de {inicio:%d/%m}"))
        return intervalos

    if tipo == "meses":
        inicio_atual = hoje.replace(day=1)
        intervalos = []
        ano, mes = inicio_atual.year, inicio_atual.month
        meses = []
        for _ in range(3):
            meses.append((ano, mes))
            mes -= 1
            if mes == 0:
                ano -= 1
                mes = 12
        for ano, mes in reversed(meses):
            inicio = date(ano, mes, 1)
            if mes == 12:
                fim = date(ano + 1, 1, 1)
            else:
                fim = date(ano, mes + 1, 1)
            nomes_meses = (
                "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
            )
            intervalos.append((inicio, fim, nomes_meses[mes - 1]))
        return intervalos

    return [
        (
            hoje - timedelta(days=recuo),
            hoje - timedelta(days=recuo) + timedelta(days=1),
            (hoje - timedelta(days=recuo)).strftime("%d/%m"),
        )
        for recuo in (2, 1, 0)
    ]


def _inicio_fuso(data):
    instante = datetime.combine(data, time.min)
    if timezone.is_aware(timezone.now()):
        return timezone.make_aware(instante, timezone.get_current_timezone())
    return instante


def dashboard(request):
    periodo = request.GET.get("periodo", "dias")
    if periodo not in ("dias", "semanas", "meses"):
        periodo = "dias"

    hoje = timezone.localdate()
    periodos = _periodos_comparacao(periodo, hoje)
    vendas = Venda.objects.all()

    def mais_vendidos(tipo):
        return list(
            ItemVenda.objects.filter(tipo=tipo)
            .values("descricao")
            .annotate(quantidade=Sum("quantidade"))
            .order_by("-quantidade", "descricao")[:3]
        )

    produtos_mais_vendidos = mais_vendidos(ItemVenda.Tipo.PRODUTO)
    servicos_mais_vendidos = mais_vendidos(ItemVenda.Tipo.SERVICO)

    pagamentos = list(
        vendas.values("forma_pagamento")
        .annotate(total=Sum("total"))
        .order_by("-total", "forma_pagamento")[:3]
    )
    forma_pagamento_labels = dict(Venda.FormaPagamento.choices)

    produtos_baixo_estoque = list(
        Produto.objects.filter(quantidade__lt=5)
        .order_by("quantidade", "descricao")
        .values("descricao", "quantidade")
    )
    quantidade_estoque_baixo = len(produtos_baixo_estoque)
    quantidade_estoque_normal = Produto.objects.filter(quantidade__gte=5).count()

    inicio_consulta = _inicio_fuso(periodos[0][0])
    fim_consulta = _inicio_fuso(periodos[-1][1])
    vendas_no_periodo = list(
        vendas.filter(criada_em__gte=inicio_consulta, criada_em__lt=fim_consulta)
        .values_list("criada_em", "total")
    )
    valores_por_periodo = []
    for inicio, fim, rotulo in periodos:
        inicio_aware = _inicio_fuso(inicio)
        fim_aware = _inicio_fuso(fim)
        total = sum(
            (
                valor
                for criada_em, valor in vendas_no_periodo
                if inicio_aware <= criada_em < fim_aware
            ),
            Decimal("0.00"),
        )
        valores_por_periodo.append(float(total))

    return render(
        request,
        "dashboard.html",
        {
            "periodo": periodo,
            "produtos_mais_vendidos": produtos_mais_vendidos,
            "servicos_mais_vendidos": servicos_mais_vendidos,
            "pagamentos_labels": [
                forma_pagamento_labels[item["forma_pagamento"]]
                for item in pagamentos
            ],
            "pagamentos_valores": [float(item["total"]) for item in pagamentos],
            "produtos_baixo_estoque": produtos_baixo_estoque,
            "quantidade_estoque_baixo": quantidade_estoque_baixo,
            "quantidade_estoque_normal": quantidade_estoque_normal,
            "periodo_labels": [item[2] for item in periodos],
            "periodo_valores": valores_por_periodo,
        },
    )


class DataRelatorioForm(forms.Form):
    data = forms.DateField(
        required=True,
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )


def relatorio_caixa(request):
    dados_form = request.GET or {"data": timezone.localdate().isoformat()}
    form = DataRelatorioForm(dados_form)
    vendas = Venda.objects.none()
    total = Decimal("0.00")
    pagamentos = []
    if form.is_valid():
        data = form.cleaned_data["data"]
        inicio = _inicio_fuso(data)
        fim = _inicio_fuso(data + timedelta(days=1))
        vendas = (
            Venda.objects.filter(criada_em__gte=inicio, criada_em__lt=fim)
            .prefetch_related("itens")
            .order_by("criada_em", "id")
        )
        total = vendas.aggregate(total=Sum("total"))["total"] or Decimal("0.00")
        pagamentos = list(
            vendas.values("forma_pagamento")
            .annotate(total=Sum("total"))
            .order_by("forma_pagamento")
        )

    return render(
        request,
        "relatorios/caixa.html",
        {
            "form": form,
            "vendas": vendas,
            "total": total,
            "pagamentos": pagamentos,
            "forma_pagamento_labels": dict(Venda.FormaPagamento.choices),
            "data_selecionada": form.cleaned_data.get("data") if form.is_valid() else None,
            "consultado": form.is_valid(),
        },
    )


def relatorio_estoque(request):
    produtos = list(Produto.objects.order_by("descricao"))
    for produto in produtos:
        produto.status_estoque = (
            "Em falta"
            if produto.quantidade == 0
            else "Baixo"
            if produto.quantidade <= 5
            else "Adequado"
        )
    return render(
        request,
        "relatorios/estoque.html",
        {
            "produtos": produtos,
            "total_produtos": len(produtos),
            "produtos_em_falta": sum(p.quantidade == 0 for p in produtos),
            "produtos_em_baixa": sum(0 < p.quantidade <= 5 for p in produtos),
        },
    )
