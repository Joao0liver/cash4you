from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProdutoForm
from .models import Produto


def produto(request):
    busca = request.GET.get("q", "").strip()
    ordenar = request.GET.get("ordenar", "descricao_asc")
    ordenacoes = {
        "descricao_asc": ("descricao", "id"),
        "descricao_desc": ("-descricao", "-id"),
        "quantidade_asc": ("quantidade", "descricao", "id"),
        "quantidade_desc": ("-quantidade", "descricao", "id"),
    }
    if ordenar not in ordenacoes:
        ordenar = "descricao_asc"

    produtos = Produto.objects.all()

    if busca:
        filtros = Q(descricao__icontains=busca)
        try:
            valor = Decimal(busca.replace(",", "."))
        except InvalidOperation:
            pass
        else:
            filtros |= Q(preco_custo=valor) | Q(preco_venda=valor)

        if busca.isdigit():
            filtros |= Q(quantidade=int(busca))

        produtos = produtos.filter(filtros)

    produtos = list(produtos.order_by(*ordenacoes[ordenar]))
    quantidade_total = 0
    valor_estoque_total = Decimal("0.00")
    lucro_estoque_total = Decimal("0.00")
    produtos_sem_despesas_cadastradas = 0

    for produto_obj in produtos:
        valor_estoque = produto_obj.preco_venda * produto_obj.quantidade
        produto_obj.valor_estoque = valor_estoque.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        quantidade_total += produto_obj.quantidade
        valor_estoque_total += produto_obj.valor_estoque

        if produto_obj.despesas_variaveis_percentual is None:
            produto_obj.lucro_liquido_unitario = None
            produto_obj.lucro_liquido_estoque = None
            produtos_sem_despesas_cadastradas += 1
            continue

        despesas_unitarias = (
            produto_obj.preco_venda
            * produto_obj.despesas_variaveis_percentual
            / Decimal("100")
        )
        produto_obj.lucro_liquido_unitario = (
            produto_obj.preco_venda - produto_obj.preco_custo - despesas_unitarias
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        produto_obj.lucro_liquido_estoque = (
            produto_obj.lucro_liquido_unitario * produto_obj.quantidade
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        lucro_estoque_total += produto_obj.lucro_liquido_estoque

    return render(
        request,
        "listar_produto.html",
        {
            "produtos": produtos,
            "busca": busca,
            "ordenar": ordenar,
            "quantidade_total": quantidade_total,
            "valor_estoque_total": valor_estoque_total,
            "lucro_estoque_total": lucro_estoque_total,
            "produtos_sem_despesas_cadastradas": produtos_sem_despesas_cadastradas,
        },
    )


def criar_produto(request):
    form = ProdutoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("listar_produto")

    return render(
        request,
        "form_produto.html",
        {"form": form, "titulo": "Novo produto", "botao": "Cadastrar"},
    )


def editar_produto(request, pk):
    produto_obj = get_object_or_404(Produto, pk=pk)
    form = ProdutoForm(request.POST or None, instance=produto_obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("listar_produto")

    return render(
        request,
        "form_produto.html",
        {"form": form, "titulo": "Editar produto", "botao": "Salvar alterações"},
    )


def excluir_produto(request, pk):
    produto_obj = get_object_or_404(Produto, pk=pk)
    if request.method == "POST":
        produto_obj.delete()
        return redirect("listar_produto")

    return render(
        request,
        "confirmar_exclusao_produto.html",
        {"produto": produto_obj},
    )
