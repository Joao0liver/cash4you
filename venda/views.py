from decimal import Decimal
from urllib.parse import quote

from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from produto.models import Produto
from servico.models import Servico

from .forms import EditarVendaForm, FinalizarVendaForm
from .models import ItemVenda, Venda


CART_SESSION_KEY = "venda_cart"


class EstoqueInsuficiente(Exception):
    pass


def _formatar_moeda(valor):
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _carrinho_sessao(request):
    return dict(request.session.get(CART_SESSION_KEY, {}))


def _salvar_carrinho(request, carrinho):
    request.session[CART_SESSION_KEY] = carrinho
    request.session.modified = True


def _obter_item(tipo, item_id):
    if tipo == ItemVenda.Tipo.PRODUTO:
        return Produto.objects.filter(pk=item_id).first()
    if tipo == ItemVenda.Tipo.SERVICO:
        return Servico.objects.filter(pk=item_id).first()
    return None


def _montar_carrinho(request):
    carrinho = _carrinho_sessao(request)
    linhas = []
    total = Decimal("0.00")
    invalido = False
    for chave, quantidade in carrinho.items():
        try:
            tipo, item_id = chave.split(":", 1)
            quantidade = int(quantidade)
            item_id = int(item_id)
        except (ValueError, TypeError):
            invalido = True
            linhas.append(
                {
                    "chave": chave,
                    "disponivel": False,
                    "descricao": "Item inválido ou removido do cadastro",
                    "quantidade": quantidade,
                }
            )
            continue

        item = _obter_item(tipo, item_id)
        if item is None or quantidade < 1:
            invalido = True
            linhas.append(
                {
                    "chave": chave,
                    "disponivel": False,
                    "descricao": "Item inválido ou removido do cadastro",
                    "quantidade": quantidade,
                }
            )
            continue

        preco = item.preco_venda
        subtotal = preco * quantidade
        total += subtotal
        linhas.append(
            {
                "chave": chave,
                "tipo": tipo,
                "descricao": item.descricao,
                "preco_unitario": preco,
                "quantidade": quantidade,
                "subtotal": subtotal,
                "disponivel": True,
                "estoque": item.quantidade if tipo == ItemVenda.Tipo.PRODUTO else None,
            }
        )
    return linhas, total, invalido


def _render_caixa(request, form=None):
    linhas, total, invalido = _montar_carrinho(request)
    if form is None:
        form = FinalizarVendaForm(total=total)
    return render(
        request,
        "venda/caixa.html",
        {
            "linhas": linhas,
            "total": total,
            "form": form,
            "invalido": invalido,
            "produtos": Produto.objects.order_by("descricao"),
            "servicos": Servico.objects.order_by("descricao"),
        },
    )


def caixa(request):
    carrinho = _carrinho_sessao(request)
    if request.method == "POST":
        acao = request.POST.get("acao")

        if acao == "adicionar":
            tipo = request.POST.get("tipo")
            item_id = request.POST.get("item_id")
            try:
                item_id = int(item_id)
            except (TypeError, ValueError):
                return HttpResponseBadRequest("Item inválido.")
            item = _obter_item(tipo, item_id)
            if item is None:
                messages.error(request, "O item selecionado não existe mais.")
            else:
                chave = f"{tipo}:{item.pk}"
                quantidade = int(carrinho.get(chave, 0)) + 1
                if tipo == ItemVenda.Tipo.PRODUTO and quantidade > item.quantidade:
                    messages.error(
                        request,
                        f"Estoque insuficiente para {item.descricao}. "
                        f"Disponível: {item.quantidade}.",
                    )
                else:
                    carrinho[chave] = quantidade
                    _salvar_carrinho(request, carrinho)
                    messages.success(request, f"{item.descricao} adicionado ao carrinho.")
            return redirect("caixa")

        if acao == "atualizar":
            chave = request.POST.get("chave", "")
            try:
                tipo, item_id = chave.split(":", 1)
                item = _obter_item(tipo, int(item_id))
                quantidade = int(request.POST.get("quantidade", ""))
            except (ValueError, TypeError):
                item = None
                quantidade = 0
            if chave not in carrinho or item is None or quantidade < 1:
                messages.error(request, "Informe uma quantidade válida para um item do carrinho.")
            elif tipo == ItemVenda.Tipo.PRODUTO and quantidade > item.quantidade:
                messages.error(
                    request,
                    f"Estoque insuficiente para {item.descricao}. "
                    f"Disponível: {item.quantidade}.",
                )
            else:
                carrinho[chave] = quantidade
                _salvar_carrinho(request, carrinho)
            return redirect("caixa")

        if acao == "remover":
            chave = request.POST.get("chave", "")
            if chave in carrinho:
                del carrinho[chave]
                _salvar_carrinho(request, carrinho)
                messages.success(request, "Item removido do carrinho.")
            return redirect("caixa")

        if acao == "finalizar":
            linhas, total, invalido = _montar_carrinho(request)
            if not linhas or invalido:
                messages.error(
                    request,
                    "O carrinho está vazio ou contém itens inválidos. Revise a lista antes de finalizar.",
                )
                return redirect("caixa")

            form = FinalizarVendaForm(request.POST, total=total)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        venda = Venda.objects.create(
                            forma_pagamento=form.cleaned_data["forma_pagamento"],
                            telefone_whatsapp=form.cleaned_data["telefone_whatsapp"],
                            total=total,
                            valor_recebido=(
                                form.cleaned_data["valor_recebido"]
                                if form.cleaned_data["forma_pagamento"]
                                == Venda.FormaPagamento.DINHEIRO
                                else None
                            ),
                            troco=(
                                form.cleaned_data["valor_recebido"] - total
                                if form.cleaned_data["forma_pagamento"]
                                == Venda.FormaPagamento.DINHEIRO
                                else Decimal("0.00")
                            ),
                        )
                        for linha in linhas:
                            tipo, item_id = linha["chave"].split(":", 1)
                            if tipo == ItemVenda.Tipo.PRODUTO:
                                atualizado = Produto.objects.filter(
                                    pk=item_id,
                                    quantidade__gte=linha["quantidade"],
                                ).update(quantidade=F("quantidade") - linha["quantidade"])
                                if atualizado != 1:
                                    raise EstoqueInsuficiente(
                                        f"Estoque insuficiente para {linha['descricao']}; "
                                        "a venda não foi concluída."
                                    )
                                produto = Produto.objects.get(pk=item_id)
                                ItemVenda.objects.create(
                                    venda=venda,
                                    tipo=tipo,
                                    produto=produto,
                                    descricao=linha["descricao"],
                                    preco_unitario=linha["preco_unitario"],
                                    quantidade=linha["quantidade"],
                                    subtotal=linha["subtotal"],
                                )
                            else:
                                ItemVenda.objects.create(
                                    venda=venda,
                                    tipo=tipo,
                                    servico=Servico.objects.get(pk=item_id),
                                    descricao=linha["descricao"],
                                    preco_unitario=linha["preco_unitario"],
                                    quantidade=linha["quantidade"],
                                    subtotal=linha["subtotal"],
                                )
                except EstoqueInsuficiente as exc:
                    messages.error(request, str(exc))
                    return redirect("caixa")

                _salvar_carrinho(request, {})
                return redirect("detalhe_venda", pk=venda.pk)

            return _render_caixa(request, form=form)

        messages.error(request, "Ação inválida.")
        return redirect("caixa")

    return _render_caixa(request)


def listar_vendas(request):
    vendas = Venda.objects.prefetch_related("itens")
    return render(request, "venda/listar_vendas.html", {"vendas": vendas})


def detalhe_venda(request, pk):
    venda = get_object_or_404(
        Venda.objects.prefetch_related("itens"),
        pk=pk,
    )
    whatsapp_url = None
    if venda.telefone_whatsapp:
        mensagem = [
            f"Resumo da venda #{venda.pk}",
            *[
                f"{item.descricao} x {item.quantidade} — R$ {_formatar_moeda(item.subtotal)}"
                for item in venda.itens.all()
            ],
            f"Total: R$ {_formatar_moeda(venda.total)}",
            f"Pagamento: {venda.get_forma_pagamento_display()}",
        ]
        if venda.valor_recebido is not None:
            mensagem.extend(
                [
                    f"Valor recebido: R$ {_formatar_moeda(venda.valor_recebido)}",
                    f"Troco: R$ {_formatar_moeda(venda.troco)}",
                ]
            )
        telefone = venda.telefone_whatsapp
        numero_whatsapp = f"55{telefone}" if len(telefone) in (10, 11) else telefone
        whatsapp_url = (
            f"https://wa.me/{numero_whatsapp}?text={quote(chr(10).join(mensagem))}"
        )
    return render(
        request,
        "venda/detalhe_venda.html",
        {"venda": venda, "whatsapp_url": whatsapp_url},
    )


def editar_venda(request, pk):
    venda = get_object_or_404(
        Venda.objects.prefetch_related("itens"),
        pk=pk,
    )
    form = EditarVendaForm(request.POST or None, venda=venda)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                venda = Venda.objects.select_for_update().get(pk=venda.pk)
                itens_antigos = list(venda.itens.select_related("produto", "servico"))
                for item in itens_antigos:
                    if item.produto_id:
                        Produto.objects.filter(pk=item.produto_id).update(
                            quantidade=F("quantidade") + item.quantidade
                        )

                for tipo, catalogo_item, quantidade in form.itens_selecionados():
                    if tipo == ItemVenda.Tipo.PRODUTO:
                        atualizado = Produto.objects.filter(
                            pk=catalogo_item.pk,
                            quantidade__gte=quantidade,
                        ).update(quantidade=F("quantidade") - quantidade)
                        if atualizado != 1:
                            raise EstoqueInsuficiente(
                                f"Estoque insuficiente para {catalogo_item.descricao}; "
                                "a edição não foi salva."
                            )

                venda.forma_pagamento = form.cleaned_data["forma_pagamento"]
                venda.telefone_whatsapp = form.cleaned_data["telefone_whatsapp"]
                venda.total = form.total
                if venda.forma_pagamento == Venda.FormaPagamento.DINHEIRO:
                    venda.valor_recebido = form.cleaned_data["valor_recebido"]
                    venda.troco = venda.valor_recebido - venda.total
                else:
                    venda.valor_recebido = None
                    venda.troco = Decimal("0.00")
                venda.save()

                venda.itens.all().delete()
                for tipo, catalogo_item, quantidade in form.itens_selecionados():
                    preco = catalogo_item.preco_venda
                    ItemVenda.objects.create(
                        venda=venda,
                        tipo=tipo,
                        produto=catalogo_item if tipo == ItemVenda.Tipo.PRODUTO else None,
                        servico=catalogo_item if tipo == ItemVenda.Tipo.SERVICO else None,
                        descricao=catalogo_item.descricao,
                        preco_unitario=preco,
                        quantidade=quantidade,
                        subtotal=preco * quantidade,
                    )
        except EstoqueInsuficiente as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, "Venda atualizada com sucesso.")
            return redirect("detalhe_venda", pk=venda.pk)

    return render(
        request,
        "venda/editar_venda.html",
        {
            "venda": venda,
            "form": form,
            "produto_campos": form.produto_campos,
            "servico_campos": form.servico_campos,
        },
    )


def excluir_venda(request, pk):
    venda = get_object_or_404(
        Venda.objects.prefetch_related("itens"),
        pk=pk,
    )
    if request.method == "POST":
        with transaction.atomic():
            venda = Venda.objects.select_for_update().get(pk=venda.pk)
            for item in venda.itens.all():
                if item.produto_id:
                    Produto.objects.filter(pk=item.produto_id).update(
                        quantidade=F("quantidade") + item.quantidade
                    )
            venda.delete()
        messages.success(request, "Venda excluída e estoque dos produtos reposto.")
        return redirect("listar_vendas")

    return render(request, "venda/confirmar_exclusao.html", {"venda": venda})
