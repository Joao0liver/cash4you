from datetime import date, datetime, time
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format

from produto.models import Produto
from servico.models import Servico

from .models import DadosEstabelecimento, ItemVenda, PagamentoVenda, Venda


class CaixaTests(TestCase):
    def setUp(self):
        self.produto = Produto.objects.create(
            descricao="Shampoo",
            preco_custo="10.00",
            preco_venda="25.00",
            quantidade=5,
        )
        self.servico = Servico.objects.create(
            descricao="Corte",
            custo_direto="8.00",
            preco_venda="40.00",
        )

    def adicionar(self, tipo, item):
        return self.client.post(
            reverse("caixa"),
            {"acao": "adicionar", "tipo": tipo, "item_id": item.pk},
        )

    def finalizar(self, **dados):
        return self.client.post(
            reverse("caixa"),
            {"acao": "finalizar", "forma_pagamento": "pix", **dados},
        )

    def test_register_displays_products_and_services(self):
        response = self.client.get(reverse("caixa"))

        self.assertContains(response, "Shampoo")
        self.assertContains(response, "Corte")
        self.assertContains(response, "Carrinho")
        self.assertContains(response, "Buscar produto")
        self.assertContains(response, "Buscar serviço")
        self.assertContains(response, 'id="produto-selecionado"')
        self.assertContains(response, 'id="servico-selecionado"')
        self.assertContains(response, "Últimas vendas")
        self.assertContains(response, "Ainda não há vendas registradas.")
        response = self.adicionar("produto", self.produto)
        response = self.client.get(response.url)
        self.assertNotContains(response, "adicionado ao carrinho")

    def test_cashier_shows_only_three_most_recent_sales(self):
        vendas = []
        for indice in range(4):
            venda = Venda.objects.create(
                forma_pagamento=Venda.FormaPagamento.PIX,
                nome_cliente=f"Cliente {indice}",
                total=Decimal("25.00"),
            )
            ItemVenda.objects.create(
                venda=venda,
                tipo=ItemVenda.Tipo.PRODUTO,
                produto=self.produto,
                descricao=f"Produto {indice}",
                preco_unitario=Decimal("25.00"),
                quantidade=1,
                subtotal=Decimal("25.00"),
            )
            vendas.append(venda)

        response = self.client.get(reverse("caixa"))

        self.assertEqual(
            list(response.context["vendas_recentes"]),
            list(reversed(vendas[-3:])),
        )
        for venda in vendas[-3:]:
            self.assertContains(response, f"Venda #{venda.pk}")
            self.assertContains(response, venda.nome_cliente)
            self.assertContains(response, f"Produto {int(venda.nome_cliente[-1])}")
            self.assertContains(response, reverse("detalhe_venda", args=[venda.pk]))
        self.assertNotContains(response, "Cliente 0")

    def test_payment_controls_remain_visible_when_cart_is_empty(self):
        response = self.client.get(reverse("caixa"))

        self.assertContains(response, "Total")
        self.assertContains(response, "Finalizar venda")
        self.assertContains(response, 'name="forma_pagamento"')
        self.assertContains(response, 'id="valor-recebido"')
        self.assertContains(response, "campoDinheiro.hidden = !dinheiro;")
        self.assertContains(response, "areaTroco.hidden = !dinheiro;")
        self.assertContains(
            response,
            'id="painel-pagamentos-multiplos" class="checkout-payment-card p-3 mb-3" hidden',
        )
        self.assertContains(response, 'name="telefone_whatsapp"')
        self.assertContains(response, 'name="nome_cliente"')
        self.assertContains(response, reverse("configurar_estabelecimento"))
        self.assertContains(response, "bi-gear")
        self.assertNotContains(response, 'name="horario_funcionamento"')
        self.assertNotContains(response, 'name="endereco"')
        self.assertContains(
            response,
            '<button type="submit" class="btn btn-primary w-100" disabled>Finalizar venda</button>',
        )

    def test_establishment_details_can_be_saved_and_reused(self):
        response = self.client.post(
            reverse("configurar_estabelecimento"),
            {
                "nome": "Ateliê Cash4You",
                "horario_funcionamento": "Segunda a sexta, 9h às 18h",
                "endereco": "Rua Central, 123, Itajubá",
            },
        )

        self.assertRedirects(response, reverse("configurar_estabelecimento"))
        dados = DadosEstabelecimento.objects.get(pk=1)
        self.assertEqual(dados.nome, "Ateliê Cash4You")
        self.assertEqual(dados.horario_funcionamento, "Segunda a sexta, 9h às 18h")
        self.assertEqual(dados.endereco, "Rua Central, 123, Itajubá")

        configuracoes = self.client.get(reverse("configurar_estabelecimento"))
        self.assertContains(configuracoes, 'value="Ateliê Cash4You"')
        self.assertContains(configuracoes, 'value="Segunda a sexta, 9h às 18h"')
        self.assertContains(configuracoes, 'value="Rua Central, 123, Itajubá"')
        self.assertContains(configuracoes, reverse("caixa"))

    def test_can_add_product_and_service_and_update_quantities(self):
        self.adicionar("produto", self.produto)
        self.adicionar("servico", self.servico)
        cart = self.client.session["venda_cart"]
        product_key = f"produto:{self.produto.pk}"

        response = self.client.post(
            reverse("caixa"),
            {
                "acao": "atualizar",
                "chave": product_key,
                "quantidade": "2",
            },
        )

        self.assertRedirects(response, reverse("caixa"))
        response = self.client.get(reverse("caixa"))
        self.assertContains(response, "R$ 90,00")
        self.assertEqual(self.client.session["venda_cart"][product_key], 2)

    def test_can_remove_cart_item(self):
        self.adicionar("produto", self.produto)

        response = self.client.post(
            reverse("caixa"),
            {"acao": "remover", "chave": f"produto:{self.produto.pk}"},
        )

        self.assertRedirects(response, reverse("caixa"))
        self.assertEqual(self.client.session.get("venda_cart", {}), {})

    def test_cash_payment_records_received_amount_change_and_reduces_stock(self):
        self.adicionar("produto", self.produto)

        response = self.finalizar(
            forma_pagamento="dinheiro",
            valor_recebido="30,50",
            telefone_whatsapp="(11) 99999-8888",
        )

        sale = Venda.objects.get()
        self.assertRedirects(response, reverse("detalhe_venda", args=[sale.pk]))
        self.assertEqual(sale.total, Decimal("25.00"))
        self.assertEqual(sale.nome_cliente, "")
        self.assertEqual(sale.valor_recebido, Decimal("30.50"))
        self.assertEqual(sale.telefone_whatsapp, "11999998888")
        self.assertEqual(sale.troco, Decimal("5.50"))
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 4)
        self.assertEqual(sale.itens.get().subtotal, Decimal("25.00"))

    def test_sale_can_be_split_across_multiple_payment_methods(self):
        self.adicionar("produto", self.produto)

        response = self.finalizar(
            forma_pagamento="dinheiro",
            valor_recebido="15,00",
            forma_pagamento_2="pix",
            valor_pagamento_2="10,00",
        )

        sale = Venda.objects.get()
        self.assertRedirects(response, reverse("detalhe_venda", args=[sale.pk]))
        self.assertEqual(sale.total, Decimal("25.00"))
        self.assertEqual(sale.valor_recebido, Decimal("25.00"))
        self.assertEqual(sale.troco, Decimal("0.00"))
        self.assertEqual(sale.pagamentos.count(), 2)
        self.assertEqual(
            list(sale.pagamentos.values_list("forma_pagamento", flat=True)),
            [Venda.FormaPagamento.DINHEIRO, Venda.FormaPagamento.PIX],
        )
        self.assertEqual(
            list(sale.pagamentos.values_list("valor", flat=True)),
            [Decimal("15.00"), Decimal("10.00")],
        )
        self.assertTrue(PagamentoVenda.objects.filter(venda=sale).exists())

    def test_multiple_payment_mode_allows_cash_change_when_cash_is_used(self):
        self.adicionar("produto", self.produto)

        response = self.finalizar(
            pagamento_multiplo="on",
            quantidade_pagamentos_adicionais="1",
            forma_pagamento_2="dinheiro",
            valor_pagamento_2="30,00",
        )

        sale = Venda.objects.get()
        self.assertRedirects(response, reverse("detalhe_venda", args=[sale.pk]))
        self.assertEqual(sale.total, Decimal("25.00"))
        self.assertEqual(sale.valor_recebido, Decimal("30.00"))
        self.assertEqual(sale.troco, Decimal("5.00"))
        self.assertEqual(sale.pagamentos.count(), 1)
        self.assertEqual(
            sale.pagamentos.get().forma_pagamento,
            Venda.FormaPagamento.DINHEIRO,
        )
        self.assertEqual(sale.pagamentos.get().troco, Decimal("5.00"))

    def test_checkout_records_mixed_sale_and_service_quantity_without_stock_change(self):
        self.adicionar("produto", self.produto)
        self.adicionar("servico", self.servico)
        service_key = f"servico:{self.servico.pk}"
        self.client.post(
            reverse("caixa"),
            {"acao": "atualizar", "chave": service_key, "quantidade": "2"},
        )

        response = self.finalizar(telefone_whatsapp="11999998888")

        sale = Venda.objects.get()
        self.assertRedirects(response, reverse("detalhe_venda", args=[sale.pk]))
        self.assertEqual(sale.total, Decimal("105.00"))
        self.assertEqual(sale.itens.count(), 2)
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 4)
        self.assertEqual(
            sale.itens.get(tipo=ItemVenda.Tipo.SERVICO).subtotal,
            Decimal("80.00"),
        )

    def test_card_and_pix_sales_do_not_require_cash_amount(self):
        for payment in ("credito", "debito", "pix"):
            with self.subTest(payment=payment):
                self.adicionar("servico", self.servico)
                response = self.finalizar(forma_pagamento=payment)
                self.assertEqual(response.status_code, 302)
                sale = Venda.objects.latest("pk")
                self.assertEqual(sale.forma_pagamento, payment)
                self.assertIsNone(sale.valor_recebido)
                self.assertEqual(sale.troco, Decimal("0.00"))

    def test_cash_payment_requires_received_amount_at_least_total(self):
        self.adicionar("produto", self.produto)

        response = self.finalizar(
            forma_pagamento="dinheiro",
            valor_recebido="20.00",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("valor_recebido", response.context["form"].errors)
        self.assertEqual(Venda.objects.count(), 0)
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 5)

    def test_insufficient_stock_blocks_checkout_and_preserves_cart(self):
        self.adicionar("produto", self.produto)
        Produto.objects.filter(pk=self.produto.pk).update(quantidade=0)

        response = self.finalizar()

        self.assertRedirects(response, reverse("caixa"))
        self.assertEqual(Venda.objects.count(), 0)
        self.assertTrue(self.client.session["venda_cart"])
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 0)

    def test_product_quantity_cannot_exceed_stock_in_cart(self):
        response = self.client.post(
            reverse("caixa"),
            {
                "acao": "atualizar",
                "chave": f"produto:{self.produto.pk}",
                "quantidade": "6",
            },
        )

        self.assertRedirects(response, reverse("caixa"))
        self.assertEqual(self.client.session.get("venda_cart", {}), {})

    def test_sale_detail_has_optional_whatsapp_message(self):
        self.adicionar("produto", self.produto)
        self.finalizar(
            telefone_whatsapp="11999998888",
            nome_cliente="Ana Souza",
        )
        sale = Venda.objects.get()

        detail = self.client.get(reverse("detalhe_venda", args=[sale.pk]))
        mensagem = parse_qs(urlparse(detail.context["whatsapp_url"]).query)["text"][0]

        self.assertContains(detail, f'href="{reverse("caixa")}"')
        self.assertContains(detail, "Voltar ao caixa")
        self.assertContains(detail, "Abrir resumo no WhatsApp")
        self.assertContains(detail, "https://wa.me/5511999998888")
        self.assertContains(detail, "Shampoo")
        self.assertEqual(sale.nome_cliente, "Ana Souza")
        self.assertIn("Olá Ana Souza,", mensagem)
        self.assertIn("Segue o comprovante de pagamento solicitado:", mensagem)
        data_completa = date_format(sale.criada_em, r"l, j \d\e F \d\e Y")
        self.assertIn(
            f"Data: {data_completa}",
            mensagem,
        )
        self.assertIn("Shampoo x 1 — R$ 25,00", mensagem)
        self.assertIn("Valor total: R$ 25,00", mensagem)
        self.assertIn("Pagamento: Pix", mensagem)
        self.assertIn("Agradecemos por sua preferência!", mensagem)
        self.assertIn("É um prazer tê-lo como nosso cliente 🤩", mensagem)
        self.assertNotIn("Troco:", mensagem)

    def test_receipt_message_includes_saved_establishment_details_and_cash_change(self):
        self.client.post(
            reverse("configurar_estabelecimento"),
            {
                "nome": "Ateliê Cash4You",
                "horario_funcionamento": "Segunda a sexta, 9h às 18h",
                "endereco": "Rua Central, 123, Itajubá",
            },
        )
        self.adicionar("produto", self.produto)
        self.finalizar(
            forma_pagamento="dinheiro",
            valor_recebido="30.00",
            telefone_whatsapp="11999998888",
            nome_cliente="Ana Souza",
        )
        venda = Venda.objects.get()

        detalhe = self.client.get(reverse("detalhe_venda", args=[venda.pk]))
        mensagem = parse_qs(urlparse(detalhe.context["whatsapp_url"]).query)["text"][0]

        self.assertIn("ATELIÊ CASH4YOU", mensagem)
        self.assertIn("Ateliê Cash4You", mensagem)
        self.assertIn("Segunda a sexta, 9h às 18h", mensagem)
        self.assertIn("Rua Central, 123, Itajubá", mensagem)
        self.assertIn("Pagamento: Dinheiro", mensagem)
        self.assertIn("Troco: R$ 5,00", mensagem)
        self.assertEqual(venda.nome_estabelecimento, "Ateliê Cash4You")
        self.assertEqual(venda.horario_funcionamento, "Segunda a sexta, 9h às 18h")
        self.assertEqual(venda.endereco_estabelecimento, "Rua Central, 123, Itajubá")

    def test_sale_without_phone_has_no_whatsapp_link(self):
        self.adicionar("produto", self.produto)
        self.finalizar()
        sale = Venda.objects.get()

        detail = self.client.get(reverse("detalhe_venda", args=[sale.pk]))

        self.assertContains(detail, "Nenhum telefone foi informado")
        self.assertNotContains(detail, "wa.me/")

    def test_sales_history_lists_completed_sales(self):
        self.adicionar("produto", self.produto)
        self.finalizar()

        response = self.client.get(reverse("listar_vendas"))

        self.assertContains(response, "Registro de Vendas")
        self.assertContains(response, "R$ 25,00")

    def test_sales_history_filters_multiple_payment_methods_and_inclusive_date_range(self):
        vendas = []
        for dia, pagamento in (
            (date(2026, 10, 1), Venda.FormaPagamento.PIX),
            (date(2026, 10, 2), Venda.FormaPagamento.DINHEIRO),
            (date(2026, 10, 3), Venda.FormaPagamento.CREDITO),
            (date(2026, 10, 2), Venda.FormaPagamento.DEBITO),
        ):
            venda = Venda.objects.create(
                forma_pagamento=pagamento,
                total=Decimal("25.00"),
            )
            instante = timezone.make_aware(
                datetime.combine(dia, time(12, 0)),
                timezone.get_current_timezone(),
            )
            Venda.objects.filter(pk=venda.pk).update(criada_em=instante)
            vendas.append(venda)

        response = self.client.get(
            reverse("listar_vendas"),
            [
                ("pagamentos", Venda.FormaPagamento.DINHEIRO),
                ("pagamentos", Venda.FormaPagamento.PIX),
                ("data_inicial", "2026-10-01"),
                ("data_final", "2026-10-02"),
            ],
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {venda.pk for venda in response.context["vendas"]},
            {vendas[0].pk, vendas[1].pk},
        )
        self.assertEqual(
            response.context["form_filtro"].cleaned_data["pagamentos"],
            [Venda.FormaPagamento.DINHEIRO, Venda.FormaPagamento.PIX],
        )
        self.assertContains(response, 'name="pagamentos"')
        self.assertContains(response, 'size="1"')
        self.assertContains(response, 'style="height: 38px"')
        self.assertContains(response, 'name="data_inicial"')
        self.assertContains(response, 'name="data_final"')

    def test_sales_history_reports_invalid_date_filters(self):
        response = self.client.get(
            reverse("listar_vendas"),
            {"data_inicial": "2026-10-03", "data_final": "2026-10-01"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form_filtro"].is_valid())
        self.assertContains(response, "A data final deve ser igual ou posterior à data inicial.")

    def test_navigation_links_to_cash_and_sales_history(self):
        response = self.client.get(reverse("caixa"))

        self.assertContains(response, "Frente de Caixa")
        self.assertContains(response, "Registro de Vendas")

    def test_sale_can_be_edited_and_product_stock_is_recalculated(self):
        self.adicionar("produto", self.produto)
        self.finalizar(telefone_whatsapp="11999998888")
        venda = Venda.objects.get()

        edit_page = self.client.get(reverse("editar_venda", args=[venda.pk]))
        self.assertEqual(edit_page.status_code, 200)
        self.assertContains(edit_page, "Editar venda")

        response = self.client.post(
            reverse("editar_venda", args=[venda.pk]),
            {
                "forma_pagamento": "dinheiro",
                "valor_recebido": "60.00",
                "telefone_whatsapp": "11999997777",
                f"produto_{self.produto.pk}": "2",
                f"servico_{self.servico.pk}": "0",
            },
        )

        self.assertRedirects(response, reverse("detalhe_venda", args=[venda.pk]))
        venda.refresh_from_db()
        self.produto.refresh_from_db()
        self.assertEqual(venda.total, Decimal("50.00"))
        self.assertEqual(venda.troco, Decimal("10.00"))
        self.assertEqual(venda.telefone_whatsapp, "11999997777")
        self.assertEqual(venda.itens.get().quantidade, 2)
        self.assertEqual(self.produto.quantidade, 3)

    def test_edit_rejects_quantity_over_stock_and_keeps_sale_and_inventory_unchanged(self):
        self.adicionar("produto", self.produto)
        self.finalizar()
        venda = Venda.objects.get()
        Produto.objects.filter(pk=self.produto.pk).update(quantidade=0)

        response = self.client.post(
            reverse("editar_venda", args=[venda.pk]),
            {
                "forma_pagamento": "pix",
                "valor_recebido": "",
                "telefone_whatsapp": "",
                f"produto_{self.produto.pk}": "2",
                f"servico_{self.servico.pk}": "0",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors[f"produto_{self.produto.pk}"])
        venda.refresh_from_db()
        self.produto.refresh_from_db()
        self.assertEqual(venda.total, Decimal("25.00"))
        self.assertEqual(venda.itens.get().quantidade, 1)
        self.assertEqual(self.produto.quantidade, 0)

    def test_deleting_sale_restores_sold_product_stock(self):
        self.adicionar("produto", self.produto)
        self.finalizar()
        venda = Venda.objects.get()
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 4)

        confirmation = self.client.get(reverse("excluir_venda", args=[venda.pk]))
        self.assertEqual(confirmation.status_code, 200)
        response = self.client.post(reverse("excluir_venda", args=[venda.pk]))

        self.assertRedirects(response, reverse("listar_vendas"))
        self.assertFalse(Venda.objects.filter(pk=venda.pk).exists())
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 5)
