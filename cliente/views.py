from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q

from .forms import ClienteForm
from .models import Cliente


def cliente(request):
    busca = request.GET.get("q", "").strip()
    clientes = Cliente.objects.all()

    if busca:
        filtros = Q(nome__icontains=busca)
        numeros = "".join(caractere for caractere in busca if caractere.isdigit())
        if numeros:
            filtros |= Q(cpf__icontains=numeros) | Q(telefone__icontains=numeros)
        clientes = clientes.filter(filtros)

    return render(
        request,
        "listar_cliente.html",
        {"clientes": clientes.order_by("nome"), "busca": busca},
    )


def criar_cliente(request):
    form = ClienteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("listar_cliente")

    return render(
        request,
        "form_cliente.html",
        {"form": form, "titulo": "Novo cliente", "botao": "Cadastrar"},
    )


def editar_cliente(request, pk):
    cliente_obj = get_object_or_404(Cliente, pk=pk)
    form = ClienteForm(request.POST or None, instance=cliente_obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("listar_cliente")

    return render(
        request,
        "form_cliente.html",
        {"form": form, "titulo": "Editar cliente", "botao": "Salvar alterações"},
    )


def excluir_cliente(request, pk):
    cliente_obj = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        cliente_obj.delete()
        return redirect("listar_cliente")

    return render(request, "confirmar_exclusao_cliente.html", {"cliente": cliente_obj})
