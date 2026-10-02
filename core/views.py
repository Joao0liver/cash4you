import calendar
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django import forms
from django.db.models import Sum
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from agenda.models import Agendamento
from cliente.models import Cliente
from conta_pagar.models import ContaPagar
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
    mes_parametro = request.GET.get("mes", "")
    try:
        mes_atual = datetime.strptime(mes_parametro, "%Y-%m").date().replace(day=1)
    except ValueError:
        mes_atual = hoje.replace(day=1)
    proximo_mes = (
        date(mes_atual.year + 1, 1, 1)
        if mes_atual.month == 12
        else date(mes_atual.year, mes_atual.month + 1, 1)
    )
    mes_anterior = (mes_atual - timedelta(days=1)).replace(day=1)
    agendamentos_por_dia = defaultdict(list)
    agendamentos_mes = (
        Agendamento.objects.filter(data__gte=mes_atual, data__lt=proximo_mes)
        .prefetch_related("horarios")
        .order_by("data", "nome")
    )
    for agendamento in agendamentos_mes:
        horarios = ", ".join(
            horario.inicio.strftime("%H:%M")
            for horario in agendamento.horarios.all()
        )
        agendamentos_por_dia[agendamento.data].append(
            {
                "nome": agendamento.nome,
                "horarios": horarios,
                "url": reverse("listar_agendamentos"),
            }
        )

    contas_por_dia = defaultdict(list)
    contas_mes = ContaPagar.objects.filter(
        vencimento__gte=mes_atual,
        vencimento__lt=proximo_mes,
    ).order_by("vencimento", "descricao")
    for conta in contas_mes:
        contas_por_dia[conta.vencimento].append(conta)

    semanas_calendario = []
    for semana in calendar.Calendar(firstweekday=0).monthdatescalendar(
        mes_atual.year,
        mes_atual.month,
    ):
        semanas_calendario.append(
            [
                {
                    "data": dia,
                    "no_mes": dia.month == mes_atual.month,
                    "hoje": dia == hoje,
                    "agendamentos": agendamentos_por_dia.get(dia, []),
                    "contas": contas_por_dia.get(dia, []),
                    "url_novo_agendamento": (
                        f"{reverse('criar_agendamento')}?data={dia.isoformat()}"
                    ),
                }
                for dia in semana
            ]
        )
    nomes_meses = (
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
    )

    periodos = _periodos_comparacao(periodo, hoje)
    vendas = Venda.objects.all()
    inicio_hoje = _inicio_fuso(hoje)
    inicio_amanha = _inicio_fuso(hoje + timedelta(days=1))
    vendas_hoje = vendas.filter(
        criada_em__gte=inicio_hoje,
        criada_em__lt=inicio_amanha,
    )
    total_vendas_hoje = vendas_hoje.aggregate(total=Sum("total"))["total"] or Decimal("0.00")

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

    produtos_mais_vendidos_hoje = list(
        ItemVenda.objects.filter(
            tipo=ItemVenda.Tipo.PRODUTO,
            venda__criada_em__gte=inicio_hoje,
            venda__criada_em__lt=inicio_amanha,
        )
        .values("descricao")
        .annotate(quantidade=Sum("quantidade"))
        .order_by("-quantidade", "descricao")[:3]
    )
    maior_quantidade_produto_hoje = max(
        (item["quantidade"] for item in produtos_mais_vendidos_hoje),
        default=0,
    )
    for item in produtos_mais_vendidos_hoje:
        item["percentual"] = round(item["quantidade"] / maior_quantidade_produto_hoje * 100)

    pagamentos_hoje = list(
        vendas_hoje.values("forma_pagamento")
        .annotate(total=Sum("total"))
        .order_by("-total", "forma_pagamento")[:3]
    )
    maior_pagamento_hoje = max(
        (item["total"] for item in pagamentos_hoje),
        default=Decimal("0.00"),
    )
    formas_pagamento_hoje = [
        {
            "forma": forma_pagamento_labels[item["forma_pagamento"]],
            "total": item["total"],
            "percentual": (
                round(item["total"] / maior_pagamento_hoje * 100)
                if maior_pagamento_hoje
                else 0
            ),
        }
        for item in pagamentos_hoje
    ]

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
            "hoje": hoje,
            "mes_calendario": mes_atual,
            "mes_calendario_nome": nomes_meses[mes_atual.month - 1],
            "mes_anterior": mes_anterior.strftime("%Y-%m"),
            "proximo_mes": proximo_mes.strftime("%Y-%m"),
            "semanas_calendario": semanas_calendario,
            "vendas_hoje": vendas_hoje.count(),
            "total_vendas_hoje": total_vendas_hoje,
            "total_clientes": Cliente.objects.count(),
            "produtos_mais_vendidos_hoje": produtos_mais_vendidos_hoje,
            "formas_pagamento_hoje": formas_pagamento_hoje,
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
