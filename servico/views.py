from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ServicoForm
from .models import Servico


def servico(request):
    busca = request.GET.get("q", "").strip()
    ordenar = request.GET.get("ordenar", "descricao_asc")
    ordenacoes = {
        "descricao_asc": ("descricao", "id"),
        "descricao_desc": ("-descricao", "-id"),
    }
    if ordenar not in ordenacoes:
        ordenar = "descricao_asc"

    servicos = Servico.objects.all()

    if busca:
        filtros = Q(descricao__icontains=busca)
        try:
            preco = Decimal(busca.replace(",", "."))
        except InvalidOperation:
            pass
        else:
            filtros |= Q(preco_venda=preco)
        servicos = servicos.filter(filtros)

    servicos = servicos.order_by(*ordenacoes[ordenar])
    servicos_sem_dados_para_lucro = 0
    for servico_obj in servicos:
        if (
            servico_obj.custo_direto is None
            or servico_obj.despesas_variaveis_percentual is None
        ):
            servico_obj.lucro_liquido = None
            servicos_sem_dados_para_lucro += 1
            continue

        despesas_variaveis = (
            servico_obj.preco_venda
            * servico_obj.despesas_variaveis_percentual
            / Decimal("100")
        )
        servico_obj.lucro_liquido = (
            servico_obj.preco_venda - servico_obj.custo_direto - despesas_variaveis
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return render(
        request,
        "listar_servico.html",
        {
            "servicos": servicos,
            "busca": busca,
            "ordenar": ordenar,
            "servicos_sem_dados_para_lucro": servicos_sem_dados_para_lucro,
        },
    )


def criar_servico(request):
    form = ServicoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("listar_servico")

    return render(
        request,
        "form_servico.html",
        {"form": form, "titulo": "Novo serviço", "botao": "Cadastrar"},
    )


def editar_servico(request, pk):
    servico_obj = get_object_or_404(Servico, pk=pk)
    form = ServicoForm(request.POST or None, instance=servico_obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("listar_servico")

    return render(
        request,
        "form_servico.html",
        {"form": form, "titulo": "Editar serviço", "botao": "Salvar alterações"},
    )


def excluir_servico(request, pk):
    servico_obj = get_object_or_404(Servico, pk=pk)
    if request.method == "POST":
        servico_obj.delete()
        return redirect("listar_servico")

    return render(
        request,
        "confirmar_exclusao_servico.html",
        {"servico": servico_obj},
    )
