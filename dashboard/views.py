import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date

from cliente.models import Cliente
from catalogo.models import Produto, Servico
from venda.models import Venda, PagamentoVenda
from vendaitem.models import VendaItem
from agenda.models import Agendamento

def obter_calendario(data_referencia, visao):

    if visao == "dia":
        inicio = data_referencia
        fim = data_referencia
        dias_semana = [
            data_referencia.strftime("%A")
        ]

    elif visao == "semana":
        inicio = data_referencia - timedelta(
            days=data_referencia.weekday()
        )
        fim = inicio + timedelta(days=6)
        dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

    else:
        inicio = data_referencia.replace(day=1)

        ultimo_dia = calendar.monthrange(
            data_referencia.year,
            data_referencia.month
        )[1]

        fim = data_referencia.replace(day=ultimo_dia)

        inicio = inicio - timedelta(days=inicio.weekday())
        fim = fim + timedelta(days=(6 - fim.weekday()))

        dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

    agendamentos = (
        Agendamento.objects
        .filter(data__range=(inicio, fim))
        .select_related("funcionario")
        .prefetch_related("horarios")
        .order_by("data", "nome")
    )

    agendamentos_por_data = {}

    for agendamento in agendamentos:
        horarios = ", ".join(
            horario.inicio.strftime("%H:%M")
            for horario in agendamento.horarios.all()
        )

        agendamentos_por_data.setdefault(
            agendamento.data, []
        ).append({
            "nome": agendamento.nome,
            "agendar_para": agendamento.agendar_para_display,
            "horarios": horarios or "—",
            "url": reverse(
                "editar_agendamento",
                kwargs={"id": agendamento.id}
            ),
        })

    semanas_calendario = []
    semana_atual = []
    dia = inicio

    while dia <= fim:
        semana_atual.append({
            "data": dia,
            "no_mes": (
                dia.month == data_referencia.month
                if visao == "mes"
                else True
            ),
            "hoje": dia == timezone.localdate(),
            "feriado": None,
            "ponto_facultativo": None,
            "agendamentos": agendamentos_por_data.get(dia, []),
            "contas": [],
            "url_novo_agendamento": (
                f"{reverse('criar_agendamento')}?data={dia.isoformat()}"
            ),
        })

        if len(semana_atual) == 7:
            semanas_calendario.append(semana_atual)
            semana_atual = []

        dia += timedelta(days=1)

    if semana_atual:
        semanas_calendario.append(semana_atual)

    return {
        "dias_semana": dias_semana,
        "semanas_calendario": semanas_calendario,
    }

@login_required
def dashboard(request):

    hoje = timezone.localdate()

    # FILTROS DO CALENDÁRIO E DO COMPARATIVO
    visao = request.GET.get("visao", "mes")

    if visao not in ("dia", "semana", "mes"):
        visao = "mes"

    periodo = request.GET.get("periodo", "dias")

    if periodo not in ("dias", "semanas", "meses"):
        periodo = "dias"

    data_referencia = (
        parse_date(request.GET.get("data", "")) or hoje
    )

    calendario = obter_calendario(
        data_referencia,
        visao
    )

    if visao == "dia":
        data_anterior = data_referencia - timedelta(days=1)
        data_proxima = data_referencia + timedelta(days=1)

    elif visao == "semana":
        data_anterior = data_referencia - timedelta(days=7)
        data_proxima = data_referencia + timedelta(days=7)

    else:
        primeiro_dia = data_referencia.replace(day=1)

        data_anterior = (
            primeiro_dia - timedelta(days=1)
        ).replace(day=1)

        ultimo_dia = calendar.monthrange(
            data_referencia.year,
            data_referencia.month
        )[1]

        data_proxima = (
            data_referencia.replace(day=ultimo_dia)
            + timedelta(days=1)
        ).replace(day=1)

    # INDICADORES GERAIS
    total_clientes = Cliente.objects.count()

    total_produtos = Produto.objects.count()

    vendas_do_dia = Venda.objects.filter(
        criada_em__date=hoje
    )

    resumo_vendas_hoje = vendas_do_dia.aggregate(
        total=Sum("total"),
        quantidade=Count("id"),
    )

    total_vendas_hoje = (
        resumo_vendas_hoje["total"] or Decimal("0.00")
    )

    vendas_hoje = resumo_vendas_hoje["quantidade"]

    # ESTOQUE
    produtos_baixo_estoque = list(
        Produto.objects.filter(
            quantidade__lt=5
        ).order_by("quantidade", "descricao").values(
            "descricao",
            "quantidade",
        )
    )

    quantidade_estoque_baixo = len(
        produtos_baixo_estoque
    )

    quantidade_estoque_normal = (
        Produto.objects.filter(quantidade__gte=5).count()
    )

    # PRODUTOS MAIS VENDIDOS HOJE
    produtos_hoje = list(
        VendaItem.objects.filter(
            venda__criada_em__date=hoje,
            item__produto__isnull=False,
        )
        .values("item__descricao")
        .annotate(
            quantidade=Sum("quantidade")
        )
        .order_by("-quantidade")[:5]
    )

    maior_quantidade = max(
        (p["quantidade"] for p in produtos_hoje),
        default=0,
    )

    produtos_mais_vendidos_hoje = [
        {
            "descricao": produto["item__descricao"],
            "quantidade": produto["quantidade"],
            "percentual": round(
                produto["quantidade"] / maior_quantidade * 100
            ) if maior_quantidade else 0,
        }
        for produto in produtos_hoje
    ]

    # FORMAS DE PAGAMENTO HOJE
    pagamentos_hoje = list(
        PagamentoVenda.objects.filter(
            venda__criada_em__date=hoje
        )
        .values("forma_pagamento")
        .annotate(total=Sum("valor"))
        .order_by("-total")
    )

    total_pagamentos_hoje = sum(
        (p["total"] or Decimal("0.00") for p in pagamentos_hoje),
        Decimal("0.00"),
    )

    formas_pagamento_hoje = []

    for pagamento in pagamentos_hoje:
        forma = dict(
            PagamentoVenda.FormaPagamento.choices
        ).get(pagamento["forma_pagamento"])

        total = pagamento["total"] or Decimal("0.00")

        formas_pagamento_hoje.append({
            "forma": forma,
            "total": total,
            "percentual": round(
                float(total / total_pagamentos_hoje * 100),
                1,
            ) if total_pagamentos_hoje else 0,
        })

    # PRODUTOS MAIS VENDIDOS (GERAL)
    produtos_mais_vendidos = list(
        VendaItem.objects.filter(
            item__produto__isnull=False
        )
        .values("item__descricao")
        .annotate(
            quantidade=Sum("quantidade")
        )
        .order_by("-quantidade")[:3]
    )

    produtos_mais_vendidos = [
        {
            "descricao": p["item__descricao"],
            "quantidade": p["quantidade"],
        }
        for p in produtos_mais_vendidos
    ]

    # SERVIÇOS MAIS PRESTADOS
    servicos_mais_vendidos = list(
        VendaItem.objects.filter(
            item__servico__isnull=False
        )
        .values("item__descricao")
        .annotate(
            quantidade=Sum("quantidade")
        )
        .order_by("-quantidade")[:3]
    )

    servicos_mais_vendidos = [
        {
            "descricao": s["item__descricao"],
            "quantidade": s["quantidade"],
        }
        for s in servicos_mais_vendidos
    ]

    # FORMAS DE PAGAMENTO (GERAL)
    pagamentos_gerais = list(
        PagamentoVenda.objects
        .values("forma_pagamento")
        .annotate(total=Sum("valor"))
        .order_by("-total")[:3]
    )

    pagamentos_labels = [
        dict(PagamentoVenda.FormaPagamento.choices).get(
            p["forma_pagamento"]
        )
        for p in pagamentos_gerais
    ]

    pagamentos_valores = [
        float(p["total"] or 0)
        for p in pagamentos_gerais
    ]

    # COMPARATIVO DO CAIXA
    periodo_labels = []
    periodo_valores = []

    if periodo == "dias":

        for i in range(2, -1, -1):
            data = hoje - timedelta(days=i)

            total = Venda.objects.filter(
                criada_em__date=data
            ).aggregate(total=Sum("total"))["total"]

            periodo_labels.append(data.strftime("%d/%m"))
            periodo_valores.append(float(total or 0))

    elif periodo == "semanas":

        inicio_semana = (
            hoje - timedelta(days=hoje.weekday())
        )

        for i in range(2, -1, -1):
            inicio = inicio_semana - timedelta(weeks=i)
            fim = inicio + timedelta(days=6)

            total = Venda.objects.filter(
                criada_em__date__range=(inicio, fim)
            ).aggregate(total=Sum("total"))["total"]

            periodo_labels.append(
                f"{inicio:%d/%m} - {fim:%d/%m}"
            )
            periodo_valores.append(float(total or 0))

    else:

        for i in range(2, -1, -1):

            ano = hoje.year
            mes = hoje.month - i

            while mes <= 0:
                mes += 12
                ano -= 1

            inicio = date(ano, mes, 1)

            ultimo_dia = calendar.monthrange(
                ano, mes
            )[1]

            fim = date(ano, mes, ultimo_dia)

            total = Venda.objects.filter(
                criada_em__date__range=(inicio, fim)
            ).aggregate(total=Sum("total"))["total"]

            periodo_labels.append(
                inicio.strftime("%m/%Y")
            )

            periodo_valores.append(float(total or 0))

    context = {
        # Indicadores
        "total_clientes": total_clientes,
        "total_produtos": total_produtos,
        "total_vendas_hoje": total_vendas_hoje,
        "vendas_hoje": vendas_hoje,

        # Estoque
        "quantidade_estoque_baixo": quantidade_estoque_baixo,
        "quantidade_estoque_normal": quantidade_estoque_normal,
        "produtos_baixo_estoque": produtos_baixo_estoque,

        # Vendas e pagamentos
        "produtos_mais_vendidos_hoje": produtos_mais_vendidos_hoje,
        "formas_pagamento_hoje": formas_pagamento_hoje,
        "produtos_mais_vendidos": produtos_mais_vendidos,
        "servicos_mais_vendidos": servicos_mais_vendidos,
        "pagamentos_labels": pagamentos_labels,
        "pagamentos_valores": pagamentos_valores,

        # Comparativo
        "periodo": periodo,
        "periodo_labels": periodo_labels,
        "periodo_valores": periodo_valores,

        # Calendário
        **calendario,
        "visao_calendario": visao,
        "data_referencia": data_referencia,
        "data_anterior": data_anterior.isoformat(),
        "data_proxima": data_proxima.isoformat(),
        "titulo_calendario": {
            "dia": data_referencia.strftime("%d/%m/%Y"),
            "semana": (
                f"Semana de "
                f"{data_referencia - timedelta(days=data_referencia.weekday()):%d/%m/%Y}"
            ),
            "mes": data_referencia.strftime("%B de %Y"),
        }[visao],
        "hoje": hoje,

        # Contas a pagar: aguardando implementação do model.
        "total_contas_pendentes": None,
        "quantidade_contas_pendentes": None,
        "total_contas_pagas": None,
        "quantidade_contas_pagas": None,
    }

    return render(request, "dashboard/home.html", context)