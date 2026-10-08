from decimal import Decimal
from urllib.parse import quote

from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.formats import date_format

from catalogo.models import Item, Produto, Servico
from vendaitem.models import VendaItem
from configuracao.models import DadosEstabelecimento

from .forms import (
    EditarVendaForm,
    FiltroVendasForm,
    FinalizarVendaForm,
)
from configuracao.forms import DadosEstabelecimentoForm

from .models import PagamentoVenda, Venda

CART_SESSION_KEY = "venda_cart"

class EstoqueInsuficiente(Exception):
    pass

def formatar_moeda(valor):
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def carrinho_sessao(request):
    return dict(request.session.get(CART_SESSION_KEY, {}))

def salvar_carrinho(request, carrinho):
    request.session[CART_SESSION_KEY] = carrinho
    request.session.modified = True

def obter_item(tipo, item_id):
    if tipo == 'produto':
        return Produto.objects.filter(id=item_id).first()
    
    if tipo == 'servico':
        return Servico.objects.filter(id=item_id).first()
    
    return None

def montar_carrinho(request):
    carrinho = carrinho_sessao(request)

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

        item = obter_item(tipo, item_id)

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
                "item_id": item_id,
                "descricao": item.descricao,
                "preco_unitario": preco,
                "quantidade": quantidade,
                "subtotal": subtotal,
                "disponivel": True,
                "estoque": item.quantidade if tipo == 'produto' else None,
            }
        )

    return linhas, total, invalido

def render_caixa(request, form=None):
    linhas, total, invalido = montar_carrinho(request)

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
            "vendas_recentes": Venda.objects.prefetch_related("itens")[:3],
        },
    )

def configurar_estabelecimento(request):
    dados_estabelecimento = DadosEstabelecimento.objects.filter(id=1).first()
    if dados_estabelecimento is None:
        dados_estabelecimento = DadosEstabelecimento(id=1)
    form = DadosEstabelecimentoForm(
        request.POST or None,
        instance=dados_estabelecimento,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(
            request,
            "Dados do estabelecimento salvos para os próximos comprovantes.",
        )
        return redirect("configurar_estabelecimento")
    return render(
        request,
        "venda/configurar_estabelecimento.html",
        {"form": form},
    )

def caixa(request):
    carrinho = carrinho_sessao(request)

    if request.method == "POST":
        acao = request.POST.get("acao")

        # ADICIONAR ITEM AO CARRINHO =======================================================
        if acao == "adicionar":
            tipo = request.POST.get("tipo")
            item_id = request.POST.get("item_id")

            try:
                item_id = int(item_id)
            except (TypeError, ValueError):
                return HttpResponseBadRequest("Item inválido.")
            
            item = obter_item(tipo, item_id)

            if item is None:
                messages.error(request, "O item selecionado não existe mais.")

            else:
                chave = f"{tipo}:{item.id}"
                quantidade = int(carrinho.get(chave, 0)) + 1

                # Somente produtos possuem controle de estoque
                if tipo == 'produto' and quantidade > item.quantidade:
                    messages.error(
                        request,
                        f"Estoque insuficiente para {item.descricao}. "
                        f"Disponível: {item.quantidade}.",
                    )

                else:
                    carrinho[chave] = quantidade
                    salvar_carrinho(request, carrinho)

            return redirect("caixa")

        # ATUALIZAR QUANTIDADE =============================================================
        if acao == "atualizar":
            chave = request.POST.get("chave", "")

            try:
                tipo, item_id = chave.split(":", 1)
                item_id = int(item_id)
                item = obter_item(tipo, item_id)
                quantidade = int(request.POST.get("quantidade", ""))
            except (ValueError, TypeError):
                item = None
                quantidade = 0
                tipo = None
                
            if chave not in carrinho or item is None or quantidade < 1:
                messages.error(request, "Informe uma quantidade válida para um item do carrinho.")

            elif tipo == 'produto' and quantidade > item.quantidade:
                messages.error(
                    request,
                    f"Estoque insuficiente para {item.descricao}. "
                    f"Disponível: {item.quantidade}.",
                )

            else:
                carrinho[chave] = quantidade
                salvar_carrinho(request, carrinho)

            return redirect("caixa")

        # REMOVER ITEM DO CARRINHO =========================================================
        if acao == "remover":
            chave = request.POST.get("chave", "")

            if chave in carrinho:
                del carrinho[chave]
                salvar_carrinho(request, carrinho)

                messages.success(request, "Item removido do carrinho.")

            return redirect("caixa")

        # FINALIZAR VENDA ==================================================================
        if acao == "finalizar":
            linhas, total, invalido = montar_carrinho(request)

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

                        # Pagamentos
                        pagamentos = form.pagamentos()

                        if not pagamentos:
                            raise ValueError("Nenhum pagamento foi informado.")

                        # Criação da venda
                        venda = Venda.objects.create(
                            nome_cliente = form.cleaned_data['nome_cliente'],
                            telefone_whatsapp = form.cleaned_data['telefone_whatsapp'],
                            total = total
                        )

                        # Criação dos pagamentos
                        for pagamento in pagamentos:
                            PagamentoVenda.objects.create(
                                venda = venda,
                                forma_pagamento = pagamento['forma_pagamento'],
                                valor = pagamento['valor'],
                                valor_recebido = pagamento.get('valor_recebido', pagamento['valor_recebido']),
                                troco = pagamento.get('troco', Decimal('0.00'))
                            )

                        # Criação dos itens da venda + baixa no estoque
                        for linha in linhas:

                            tipo, item_id = linha["chave"].split(":", 1)

                            item = Item.objects.filter(
                                id = item_id
                            ).first()

                            if item is None:
                                raise ValueError(
                                    f'O item "{linha['descricao']}" '
                                    'não existe mais no catálogo.'
                                )

                            # Produtos possuem estoque
                            if tipo == 'produto':
                                atualizado = Produto.objects.filter(
                                    id=item_id,
                                    quantidade__gte=linha["quantidade"],
                                ).update(
                                    quantidade=F("quantidade") - linha["quantidade"]
                                )

                                if atualizado != 1:
                                    raise EstoqueInsuficiente(
                                        f"Estoque insuficiente para {linha['descricao']}; "
                                        "a venda não foi concluída."
                                    )
                                
                                VendaItem.objects.create(
                                    venda = venda,
                                    item = item,
                                    quantidade = linha['quantidade'],
                                    valor_unitario = linha['preco_unitario']
                                )

                except (EstoqueInsuficiente, ValueError) as exc:
                    messages.error(request, str(exc))

                    return redirect("caixa")

                # Venda concluída com sucesso
                salvar_carrinho(request, {})

                return redirect("detalhe_venda", id=venda.id)

            # Formulário inválido
            return render_caixa(request, form=form)

        # AÇÃO INVÁLIDA ====================================================================
        messages.error(request, "Ação inválida.")

        return redirect("caixa")

    # Por GET
    return render_caixa(request)

def listar_vendas(request):
    form = FiltroVendasForm(request.GET or None)

    vendas = Venda.objects.prefetch_related("itens", 'pagamentos')

    if form.is_valid():
        pagamentos = form.cleaned_data["pagamentos"]
        data_inicial = form.cleaned_data["data_inicial"]
        data_final = form.cleaned_data["data_final"]

        if pagamentos:
            vendas = vendas.filter(pagamentos__forma_pagamento__in=pagamentos).distinct()

        if data_inicial:
            vendas = vendas.filter(criada_em__date__gte=data_inicial)

        if data_final:
            vendas = vendas.filter(criada_em__date__lte=data_final)

    return render(request, "venda/listar_vendas.html", {"vendas" : vendas, "form_filtro" : form})

def detalhe_venda(request, id):
    venda = get_object_or_404(Venda.objects.prefetch_related("itens__item", 'pagamentos'), id=id)
    pagamentos = list(venda.pagamentos.all())

    whatsapp_url = None

    if venda.telefone_whatsapp:
        data_completa = date_format(venda.criada_em, r"l, j \d\e F \d\e Y")

        pagamentos_formatados = ', '.join(
            (
                f'{pagamento.get_forma_pagamento_display()}'
                f'- R$ {formatar_moeda(pagamento.valor)}'
            )
            for pagamento in pagamentos
        )

        mensagem = [
            f"Olá {venda.nome_cliente}," if venda.nome_cliente else "Olá,",
            "Segue o comprovante de pagamento solicitado:",
            "",
            f'Data: {data_completa}',
            '',
        ]

        for item in venda.itens.all():
            subtotal = item.valor * item.quantidade

            mensagem.append(
                '',
                f'{item.item.descricao} x {item.quantidade} '
                f'- R$ {formatar_moeda(subtotal)}'
            )

        mensagem.extend([
            '',
            f'Valor total: R$ {formatar_moeda(venda.total)}'
            f'Pagamento: {pagamentos_formatados}'
        ])

        troco_total = sum(
            (pagamento.troco for pagamento in pagamentos),
            Decimal('0.00'),
        )

        if troco_total:
            mensagem.append(
                f'Troco: R$ {formatar_moeda(troco_total)}'
            )

        dados_estabelecimento = DadosEstabelecimento.objects.filter(id=1).first()

        if dados_estabelecimento:
            mensagem.extend([
                '',
                dados_estabelecimento.nome,
                dados_estabelecimento.horario_funcionamento,
                dados_estabelecimento.endereco
            ])

        telefone = venda.telefone_whatsapp

        numero_whatsapp = f"55{telefone}" if len(telefone) in (10, 11) else telefone
        whatsapp_url = (
            f"https://wa.me/{numero_whatsapp}?text={quote(chr(10).join(mensagem))}"
        )

    return render(request, "venda/detalhe_venda.html", {"venda": venda, "whatsapp_url": whatsapp_url, "pagamentos": pagamentos})

def editar_venda(request, id):
    venda = get_object_or_404(
        Venda.objects.prefetch_related("itens"),
        id=id,
    )

    form = EditarVendaForm(request.POST or None, venda=venda)

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                
                venda = Venda.objects.select_for_update().get(id=venda.id)
                itens_antigos = list(venda.itens.select_related('item'))

                for item in itens_antigos:

                    if item.produto_id:
                        Produto.objects.filter(id=item.item_id).update(
                            quantidade=F("quantidade") + item.quantidade
                        )

                for tipo, catalogo_item, quantidade in form.itens_selecionados():

                    if tipo == 'produto':
                        atualizado = Produto.objects.filter(
                            id=catalogo_item.id,
                            quantidade__gte=quantidade,
                        ).update(quantidade=F("quantidade") - quantidade)

                        if atualizado != 1:
                            raise EstoqueInsuficiente(
                                f"Estoque insuficiente para {catalogo_item.descricao}; "
                                "a edição não foi salva."
                            )

                # Atualiza os dados da venda
                venda.nome_cliente = form.cleaned_data['nome_cliente']
                venda.telefone_whatsapp = form.cleaned_data['telefone_whatsapp']
                venda.total = form.total
                venda.save()

                # Atualiza os dados de pagamento da venda
                pagamentos = form.pagamentos()

                venda.pagamentos.all().delete()

                for pagamento in pagamentos:

                    PagamentoVenda.objects.create(
                        venda = venda,
                        forma_pagamente = pagamento['forma_pagamento'],
                        valor = pagamento['valor'],
                        valor_recebido = pagamento.get('valor_recebido', pagamento['valor']),
                        troco = pagamento.get('troco', Decimal['0.00'])
                    )

                # Remove os itens antigos
                venda.itens.all().delete()

                # Cria os novos itens
                for tipo, catalogo_item, quantidade in form.itens_selecionados():

                    preco = catalogo_item.preco_venda
                    VendaItem.objects.create(
                        venda=venda,
                        item=catalogo_item,
                        quantidade=quantidade,
                        valor_unitario=preco,
                    )

        except EstoqueInsuficiente as exc:
            form.add_error(None, str(exc))

        else:
            messages.success(request, "Venda atualizada com sucesso.")

            return redirect("detalhe_venda", id=venda.id)

    return render(
        request,
        "venda/editar_venda.html",
        {
            "venda": venda,
            "form": form,
            "produto_campos": form.produto_campos,
            "servico_campos": form.servico_campos,
            "total": (
                form.total if request.method == "POST" else venda.total
            )
        },
    )

def excluir_venda(request, pk):
    venda = get_object_or_404(
        Venda.objects.prefetch_related("itens"),
        pk=pk,
    )

    if request.method == "POST":
        with transaction.atomic():

            venda = Venda.objects.select_for_update().get(id=venda.id)

            for item in venda.itens.all():
                Produto.objects.filter(
                    id=item.item_id
                ).update(
                    quantidade=F('quantidade') + item.quantidade
                )

            venda.itens.all().delete()
            venda.delete()
        
        messages.success(request, "Venda excluída e estoque dos produtos reposto.")
        
        return redirect("listar_vendas")

    return render(request, "venda/confirmar_exclusao.html", {"venda": venda})
