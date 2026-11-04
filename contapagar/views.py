from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from configuracao.models import DadosEstabelecimento

from .forms import ContaPagarForm
from .models import ContaPagar

@login_required
@permission_required("contapagar.view_contapagar", raise_exception=True)
def listar_contas(request):

    contas = ContaPagar.objects.all()
    resumo = contas.aggregate(quantidade=Count("id"), total=Sum("valor"))
    configuracao = DadosEstabelecimento.objects.filter(id=1).first()
    limite_gastos = configuracao.limite_gastos if configuracao else None
    dados_grafico_percentis = []

    for conta in contas:
        conta.percentil_teto = (
            (conta.valor / limite_gastos * Decimal("100")).quantize(Decimal("0.01"))
            if limite_gastos is not None and limite_gastos > 0
            else None
        )

        if conta.percentil_teto is not None:
            dados_grafico_percentis.append({"descricao": conta.descricao, "percentil": float(conta.percentil_teto)})

    return render(
        request,
        "contapagar/listar_contas.html",
        {
            "contas": contas,
            "hoje": timezone.localdate(),
            "quantidade_total_contas": resumo["quantidade"],
            "valor_total_contas": resumo["total"] or Decimal("0.00"),
            "limite_gastos": limite_gastos,
            "dados_grafico_percentis": dados_grafico_percentis,
        }
    )

@login_required
@permission_required("contapagar.add_contapagar", raise_exception=True)
def criar_conta(request):

    form = ContaPagarForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(
            request, 
            "Conta a pagar cadastrada."
        )

        return redirect("contapagar:listar_contas_pagar")
    
    return render(request, "contapagar/form_conta.html", {"form": form, "titulo": "Nova conta a pagar", "botao": "Cadastrar conta"})

@login_required
@permission_required("contapagar.change_contapagar", raise_exception=True)
def editar_conta(request, id):

    conta = get_object_or_404(ContaPagar, id=id)
    form = ContaPagarForm(request.POST or None, instance=conta)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(
            request, 
            "Conta a pagar atualizada."
        )

        return redirect("contapagar:listar_contas_pagar")
    
    return render(request, "contapagar/form_conta.html", {"form": form, "titulo": "Editar conta a pagar", "botao": "Salvar alterações"})

@login_required
@permission_required("contapagar.change_contapagar", raise_exception=True)
def alternar_status_conta(request, id):

    conta = get_object_or_404(ContaPagar, id=id)

    if request.method != "POST":
        return redirect("contapagar:listar_contas_pagar")
    
    if conta.paga:
        configuracao = DadosEstabelecimento.objects.filter(id=1).first()
        limite = configuracao.limite_gastos if configuracao else None
        total_pendente = (
            ContaPagar.objects.filter(paga=False).aggregate(total=Sum("valor"))["total"]
            or Decimal("0.00")
        )

        if limite is not None and total_pendente + conta.valor > limite:
            messages.error(
                request,
                f"Não foi possível reabrir a conta: isso ultrapassaria a margem máxima de gastos de R$ {limite:.2f}.",
            )

            return redirect("listar_contas_pagar")
        
    conta.paga = not conta.paga
    conta.save(update_fields=["paga"])

    return redirect("contapagar:listar_contas_pagar")

@login_required
@permission_required("contapagar.delete_contapagar", raise_exception=True)
def excluir_conta(request, id):

    conta = get_object_or_404(ContaPagar, id=id)

    if request.method == "POST":
        conta.delete()
        messages.success(
            request, 
            "Conta a pagar excluída."
        )

        return redirect("contapagar:listar_contas_pagar")
    
    return render(request, "contapagar/confirmar_exclusao.html", {"conta": conta})