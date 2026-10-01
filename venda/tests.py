from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from produto.models import Produto
from servico.models import Servico

from .models import ItemVenda, Venda


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
        self.assertContains(response, "Lista de compras")

    def test_payment_controls_remain_visible_when_cart_is_empty(self):
        response = self.client.get(reverse("caixa"))

        self.assertContains(response, 'id="forma-pagamento"')
        self.assertContains(response, 'id="valor-recebido"')
        self.assertContains(response, 'name="telefone_whatsapp"')
        self.assertContains(
            response,
            '<button type="submit" class="btn btn-primary" disabled>Finalizar pagamento</button>',
        )

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
        self.assertEqual(sale.valor_recebido, Decimal("30.50"))
        self.assertEqual(sale.troco, Decimal("5.50"))
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 4)
        self.assertEqual(sale.itens.get().subtotal, Decimal("25.00"))

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
        response = self.finalizar(telefone_whatsapp="11999998888")
        sale = Venda.objects.get()

        detail = self.client.get(reverse("detalhe_venda", args=[sale.pk]))

        self.assertContains(detail, "Abrir resumo no WhatsApp")
        self.assertContains(detail, "https://wa.me/5511999998888")
        self.assertContains(detail, "Shampoo")

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

        self.assertContains(response, "Histórico de vendas")
        self.assertContains(response, "R$ 25,00")

    def test_navigation_links_to_cash_and_sales_history(self):
        response = self.client.get(reverse("caixa"))

        self.assertContains(response, "Caixa")
        self.assertContains(response, "Histórico de vendas")

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
