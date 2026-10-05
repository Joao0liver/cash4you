from decimal import Decimal

from django.contrib import messages
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ContaPagarForm, FuncionarioForm
from .models import ContaPagar, Funcionario


def listar_contas(request):
    contas = ContaPagar.objects.all()
    resumo = contas.aggregate(quantidade=Count("pk"), total=Sum("valor"))
    return render(
        request,
        "conta_pagar/listar_contas.html",
        {
            "contas": contas,
            "hoje": timezone.localdate(),
            "quantidade_total_contas": resumo["quantidade"],
            "valor_total_contas": resumo["total"] or Decimal("0.00"),
        },
    )


def listar_funcionarios(request):
    return render(
        request,
        "conta_pagar/listar_funcionarios.html",
        {"funcionarios": Funcionario.objects.all()},
    )


def criar_funcionario(request):
    form = FuncionarioForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Funcionário cadastrado.")
        return redirect("listar_funcionarios")
    return render(
        request,
        "conta_pagar/form_funcionario.html",
        {"form": form},
    )


def criar_conta(request):
    form = ContaPagarForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Conta a pagar cadastrada.")
        return redirect("listar_contas_pagar")
    return render(
        request,
        "conta_pagar/form_conta.html",
        {"form": form, "titulo": "Nova conta a pagar", "botao": "Cadastrar conta"},
    )


def editar_conta(request, pk):
    conta = get_object_or_404(ContaPagar, pk=pk)
    form = ContaPagarForm(request.POST or None, instance=conta)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Conta a pagar atualizada.")
        return redirect("listar_contas_pagar")
    return render(
        request,
        "conta_pagar/form_conta.html",
        {"form": form, "titulo": "Editar conta a pagar", "botao": "Salvar alterações"},
    )


def alternar_status_conta(request, pk):
    conta = get_object_or_404(ContaPagar, pk=pk)
    if request.method != "POST":
        return redirect("listar_contas_pagar")
    conta.paga = not conta.paga
    conta.save(update_fields=["paga"])
    return redirect("listar_contas_pagar")


def excluir_conta(request, pk):
    conta = get_object_or_404(ContaPagar, pk=pk)
    if request.method == "POST":
        conta.delete()
        messages.success(request, "Conta a pagar excluída.")
        return redirect("listar_contas_pagar")
    return render(request, "conta_pagar/confirmar_exclusao.html", {"conta": conta})
