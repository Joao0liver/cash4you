from datetime import date, datetime, time, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from produto.models import Produto
from venda.models import ItemVenda, Venda


class PricingPageTests(TestCase):
    def test_navigation_groups_start_collapsed_and_support_single_open_menu(self):
        response = self.client.get(reverse("listar_cadastros"))

        for menu_id in ("menu-cadastrar", "menu-vendas", "menu-agenda"):
            self.assertContains(
                response,
                f'<ul id="{menu_id}" class="nav nav-pills flex-column gap-1 nav-tree" hidden>',
            )
        self.assertContains(response, 'data-nav-toggle aria-expanded="false"')
        self.assertContains(response, "fecharMenus(toggle)")

    def test_precificar_is_available_from_cadastros_page(self):
        response = self.client.get(reverse("listar_cadastros"))

        self.assertContains(response, reverse("precificar"))
        self.assertContains(response, "Precificar")

    def test_precificar_page_explains_markup(self):
        response = self.client.get(reverse("precificar"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Custo variável direto")
        self.assertContains(response, "Despesas variáveis")
        self.assertContains(response, "Lucro desejado")
        self.assertContains(response, "Preço de venda = CV")
        self.assertContains(response, "dividirá por zero")
        self.assertContains(response, "denominador será negativo")
        self.assertContains(response, "R$ 80,00 ÷ 0,70")
        self.assertContains(response, "R$ 114,29")
        self.assertContains(response, reverse("criar_produto"))
        self.assertContains(response, reverse("criar_servico"))


class DashboardTests(TestCase):
    def criar_venda(self, data, forma, total, itens=()):
        venda = Venda.objects.create(
            forma_pagamento=forma,
            total=Decimal(total),
        )
        instante = timezone.make_aware(
            datetime.combine(data, time(12, 0)),
            timezone.get_current_timezone(),
        )
        Venda.objects.filter(pk=venda.pk).update(criada_em=instante)
        for tipo, descricao, quantidade in itens:
            ItemVenda.objects.create(
                venda=venda,
                tipo=tipo,
                descricao=descricao,
                quantidade=quantidade,
                preco_unitario=Decimal(total) / quantidade,
                subtotal=Decimal(total),
            )
        return venda

    @patch("core.views.timezone.localdate", return_value=date(2026, 10, 1))
    def test_dashboard_shows_top_sellers_payments_and_low_stock(self, _localdate):
        self.criar_venda(
            date(2026, 10, 1),
            Venda.FormaPagamento.PIX,
            "100.00",
            [
                (ItemVenda.Tipo.PRODUTO, "Shampoo", 4),
                (ItemVenda.Tipo.SERVICO, "Corte", 3),
            ],
        )
        self.criar_venda(
            date(2026, 10, 1),
            Venda.FormaPagamento.DINHEIRO,
            "50.00",
            [
                (ItemVenda.Tipo.PRODUTO, "Condicionador", 2),
                (ItemVenda.Tipo.SERVICO, "Barba", 2),
            ],
        )
        Produto.objects.create(
            descricao="Shampoo",
            preco_custo="5.00",
            preco_venda="10.00",
            quantidade=3,
        )
        Produto.objects.create(
            descricao="Condicionador",
            preco_custo="5.00",
            preco_venda="10.00",
            quantidade=5,
        )

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [(item["descricao"], item["quantidade"]) for item in response.context["produtos_mais_vendidos"]],
            [("Shampoo", 4), ("Condicionador", 2)],
        )
        self.assertEqual(
            [(item["descricao"], item["quantidade"]) for item in response.context["servicos_mais_vendidos"]],
            [("Corte", 3), ("Barba", 2)],
        )
        self.assertEqual(
            response.context["pagamentos_labels"],
            ["Pix", "Dinheiro"],
        )
        self.assertEqual(
            response.context["pagamentos_valores"],
            [100.0, 50.0],
        )
        self.assertEqual(
            list(response.context["produtos_baixo_estoque"]),
            [{"descricao": "Shampoo", "quantidade": 3}],
        )
        self.assertContains(response, "Dashboards")
        self.assertContains(response, "menos de 5 unidades")
        self.assertContains(response, 'id="produtos-chart"')
        self.assertContains(response, 'id="servicos-chart"')
        self.assertContains(response, 'id="pagamentos-chart"')
        self.assertContains(response, 'id="estoque-chart"')
        self.assertContains(response, 'id="caixa-chart"')

    def test_seller_charts_limit_results_to_three_items(self):
        venda = Venda.objects.create(
            forma_pagamento=Venda.FormaPagamento.PIX,
            total=Decimal("10.00"),
        )
        for index in range(4):
            ItemVenda.objects.create(
                venda=venda,
                tipo=ItemVenda.Tipo.PRODUTO,
                descricao=f"Produto {index}",
                quantidade=4 - index,
                preco_unitario=Decimal("1.00"),
                subtotal=Decimal("10.00"),
            )
            ItemVenda.objects.create(
                venda=venda,
                tipo=ItemVenda.Tipo.SERVICO,
                descricao=f"Serviço {index}",
                quantidade=4 - index,
                preco_unitario=Decimal("1.00"),
                subtotal=Decimal("10.00"),
            )

        response = self.client.get(reverse("home"))

        self.assertEqual(len(response.context["produtos_mais_vendidos"]), 3)
        self.assertEqual(len(response.context["servicos_mais_vendidos"]), 3)

    @patch("core.views.timezone.localdate", return_value=date(2026, 10, 1))
    def test_cash_comparison_selects_three_days_weeks_or_months(self, _localdate):
        self.criar_venda(date(2026, 9, 29), Venda.FormaPagamento.PIX, "10.00")
        self.criar_venda(date(2026, 9, 30), Venda.FormaPagamento.PIX, "20.00")
        self.criar_venda(date(2026, 10, 1), Venda.FormaPagamento.PIX, "30.00")

        daily = self.client.get(reverse("home"), {"periodo": "dias"})
        weekly = self.client.get(reverse("home"), {"periodo": "semanas"})
        monthly = self.client.get(reverse("home"), {"periodo": "meses"})

        self.assertEqual(daily.context["periodo_labels"], ["29/09", "30/09", "01/10"])
        self.assertEqual(daily.context["periodo_valores"], [10.0, 20.0, 30.0])
        self.assertEqual(
            weekly.context["periodo_labels"],
            ["Semana de 14/09", "Semana de 21/09", "Semana de 28/09"],
        )
        self.assertEqual(weekly.context["periodo_valores"], [0.0, 0.0, 60.0])
        self.assertEqual(
            monthly.context["periodo_labels"],
            ["Agosto", "Setembro", "Outubro"],
        )
        self.assertEqual(monthly.context["periodo_valores"], [0.0, 30.0, 30.0])
        self.assertEqual(monthly.context["periodo"], "meses")

    def test_unknown_dashboard_period_falls_back_to_days(self):
        response = self.client.get(reverse("home"), {"periodo": "invalid"})

        self.assertEqual(response.context["periodo"], "dias")


class ReportsTests(TestCase):
    def criar_venda(self, instante, total, forma=Venda.FormaPagamento.PIX):
        venda = Venda.objects.create(forma_pagamento=forma, total=Decimal(total))
        Venda.objects.filter(pk=venda.pk).update(criada_em=instante)
        return venda

    def test_daily_cash_report_defaults_to_today_and_can_select_date(self):
        hoje = timezone.localdate()
        ontem = hoje - timedelta(days=1)
        instante_hoje = timezone.make_aware(
            datetime.combine(hoje, time(12)),
            timezone.get_current_timezone(),
        )
        instante_ontem = timezone.make_aware(
            datetime.combine(ontem, time(12)),
            timezone.get_current_timezone(),
        )
        venda_hoje = self.criar_venda(instante_hoje, "120.50")
        venda_ontem = self.criar_venda(
            instante_ontem,
            "25.00",
            Venda.FormaPagamento.DINHEIRO,
        )
        ItemVenda.objects.create(
            venda=venda_hoje,
            tipo=ItemVenda.Tipo.PRODUTO,
            descricao="Shampoo",
            preco_unitario=Decimal("120.50"),
            quantidade=1,
            subtotal=Decimal("120.50"),
        )

        hoje_response = self.client.get(reverse("relatorio_caixa"))
        ontem_response = self.client.get(
            reverse("relatorio_caixa"),
            {"data": ontem.isoformat()},
        )

        self.assertEqual(hoje_response.context["total"], Decimal("120.50"))
        self.assertContains(hoje_response, "Imprimir relatório")
        self.assertContains(hoje_response, "Shampoo")
        self.assertEqual(ontem_response.context["total"], Decimal("25.00"))
        self.assertEqual(ontem_response.context["vendas"].count(), 1)

    def test_invalid_daily_cash_report_date_is_reported(self):
        response = self.client.get(reverse("relatorio_caixa"), {"data": "invalid"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["data"])
        self.assertIsNone(response.context["data_selecionada"])

    def test_inventory_report_marks_low_and_out_of_stock_products(self):
        Produto.objects.create(
            descricao="Em falta",
            preco_custo="5.00",
            preco_venda="10.00",
            quantidade=0,
        )
        Produto.objects.create(
            descricao="Estoque baixo",
            preco_custo="5.00",
            preco_venda="10.00",
            quantidade=5,
        )
        Produto.objects.create(
            descricao="Adequado",
            preco_custo="5.00",
            preco_venda="10.00",
            quantidade=6,
        )

        response = self.client.get(reverse("relatorio_estoque"))
        produtos = {produto.descricao: produto for produto in response.context["produtos"]}

        self.assertEqual(response.context["produtos_em_falta"], 1)
        self.assertEqual(response.context["produtos_em_baixa"], 1)
        self.assertEqual(produtos["Em falta"].status_estoque, "Em falta")
        self.assertEqual(produtos["Estoque baixo"].status_estoque, "Baixo")
        self.assertEqual(produtos["Adequado"].status_estoque, "Adequado")
        self.assertContains(response, "Imprimir relatório")

    def test_reports_are_available_from_navigation(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, reverse("relatorio_caixa"))
        self.assertContains(response, reverse("relatorio_estoque"))
