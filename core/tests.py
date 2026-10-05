from datetime import date, datetime, time, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from agenda.models import Agendamento, HorarioAgendado
from cliente.models import Cliente
from conta_pagar.models import ContaPagar, Funcionario
from produto.models import Produto
from venda.models import ItemVenda, Venda


class PricingPageTests(TestCase):
    def test_navigation_groups_start_collapsed_and_support_single_open_menu(self):
        response = self.client.get(reverse("listar_cadastros"))

        for menu_id in (
            "menu-cadastrar",
            "menu-vendas",
            "menu-agenda",
            "menu-relatorios",
            "menu-configuracoes",
        ):
            self.assertContains(
                response,
                f'<ul id="{menu_id}" class="nav nav-pills flex-column gap-1 nav-tree" hidden>',
            )
        self.assertContains(response, 'aria-expanded="false"')
        self.assertContains(response, "fecharMenus(toggle)")
        self.assertContains(response, "function abrirMenu(toggle)")
        self.assertContains(response, "const caminhoAtual = window.location.pathname")
        self.assertContains(response, "caminho.length > tamanhoCaminhoMenuAtual")

    def test_cadastrar_opens_the_form_choices_without_a_legacy_overview_link(self):
        response = self.client.get(reverse("listar_cadastros"))

        self.assertContains(response, f'href="{reverse("listar_cadastros")}"')
        self.assertNotContains(response, ">Visão geral<")
        for label in (
            "Produtos no Estoque",
            "Serviços Prestados",
            "Carteira de Clientes",
            "Funcionários",
            "Contas a pagar",
        ):
            self.assertContains(response, label)
        self.assertContains(response, f'href="{reverse("listar_funcionarios")}"')
        self.assertContains(response, f'href="{reverse("listar_contas_pagar")}"')
        self.assertNotContains(response, ">Precificar<")

    def test_vendas_link_opens_cashier_and_keeps_sales_menu_expanded(self):
        response = self.client.get(reverse("caixa"))

        self.assertRegex(
            response.content.decode(),
            rf'<a href="{reverse("caixa")}" class="nav-link text-white flex-grow-1">\s*Vendas\s*</a>',
        )
        self.assertContains(
            response,
            f'<a href="{reverse("caixa")}" class="nav-link active">\n                                    Frente de Caixa',
        )
        self.assertContains(
            response,
            'data-nav-paths="/vendas/" aria-label="Abrir menu Vendas" aria-expanded="false" aria-controls="menu-vendas"',
        )
        self.assertContains(response, "const caminhoAtual = window.location.pathname")
        self.assertContains(response, "if (menuAtual) abrirMenu(menuAtual)")

    def test_agenda_link_opens_appointments_and_only_appointments_are_selected(self):
        response = self.client.get(reverse("listar_agendamentos"))

        self.assertRegex(
            response.content.decode(),
            rf'<a href="{reverse("listar_agendamentos")}" class="nav-link text-white flex-grow-1">\s*Agenda\s*</a>',
        )
        self.assertContains(
            response,
            f'<a href="{reverse("listar_agendamentos")}" class="nav-link active">\n                                    Agendamentos',
        )
        self.assertNotContains(response, "class=\"nav-link text-white flex-grow-1 active\"")
        self.assertContains(
            response,
            'data-nav-paths="/agenda/" aria-label="Abrir menu Agenda" aria-expanded="false" aria-controls="menu-agenda"',
        )

    def test_settings_menu_contains_establishment_and_pricing_pages(self):
        response = self.client.get(reverse("precificar"))

        self.assertRegex(
            response.content.decode(),
            rf'<a href="{reverse("configurar_estabelecimento")}" class="nav-link text-white flex-grow-1">\s*Configurações\s*</a>',
        )
        self.assertContains(response, reverse("configurar_estabelecimento"))
        self.assertContains(response, reverse("precificar"))
        self.assertContains(response, "Dados do Estabelecimento")
        self.assertContains(response, "Precificação")
        self.assertContains(
            response,
            'data-nav-paths="/configuracoes/,/vendas/configuracoes/" aria-label="Abrir menu Configurações" aria-expanded="false" aria-controls="menu-configuracoes"',
        )

    def test_payable_accounts_are_nested_in_registration_navigation(self):
        response = self.client.get(reverse("listar_contas_pagar"))

        conteudo = response.content.decode()
        link_contas = (
            f'<a href="{reverse("listar_contas_pagar")}" class="nav-link'
        )
        self.assertEqual(conteudo.count(link_contas), 1)
        self.assertContains(
            response,
            'data-nav-paths="/cadastrar/,/produto/,/servico/,/cliente/,/contas-a-pagar/funcionarios/,/contas-a-pagar/" aria-label="Abrir menu Cadastrar"',
        )
        self.assertContains(response, "Contas a pagar")
        self.assertIn('id="menu-cadastrar"', conteudo)
        self.assertLess(conteudo.index('id="menu-cadastrar"'), conteudo.index(link_contas))
        self.assertGreater(conteudo.index(link_contas), conteudo.index('id="menu-cadastrar"'))

    def test_legacy_pricing_url_redirects_to_settings(self):
        response = self.client.get("/cadastrar/precificar/")

        self.assertRedirects(response, reverse("precificar"), status_code=301)

    def test_precificar_page_explains_markup(self):
        response = self.client.get(reverse("precificar"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Precificação")
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

    def test_dashboard_indicators_link_to_destinations_with_access_tooltips(self):
        response = self.client.get(reverse("home"))

        self.assertContains(
            response,
            f'href="{reverse("listar_vendas")}" class="card shadow-sm border-0 h-100 text-decoration-none" data-bs-toggle="tooltip"',
        )
        self.assertContains(
            response,
            f'href="{reverse("listar_cliente")}" class="card shadow-sm border-0 h-100 text-decoration-none" data-bs-toggle="tooltip"',
        )
        self.assertContains(
            response,
            f'href="{reverse("listar_produto")}" class="card shadow-sm border-warning h-100 text-decoration-none" data-bs-toggle="tooltip"',
        )
        self.assertContains(response, "Acesse o histórico para consultar as vendas e seus detalhes.")
        self.assertContains(response, "Acesse o histórico para consultar a quantidade e os detalhes das vendas.")
        self.assertContains(response, "Acesse Cadastrar → Carteira de Clientes")
        self.assertContains(response, "Acesse Cadastrar → Produtos no Estoque")

    @patch("core.views.timezone.localdate", return_value=date(2026, 10, 2))
    def test_home_calendar_defaults_to_day_view(self, _localdate):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.context["visao_calendario"], "dia")
        self.assertEqual(response.context["data_referencia"], date(2026, 10, 2))
        self.assertEqual(len(response.context["semanas_calendario"]), 1)
        self.assertEqual(len(response.context["semanas_calendario"][0]), 1)
        self.assertContains(response, "Sexta-feira, 02/10/2026")
        self.assertContains(response, '<option value="dia" selected>')
        self.assertContains(response, 'title="Exibir o mês anterior no calendário"')
        self.assertContains(response, 'title="Exibir o próximo mês no calendário"')

    @patch("core.views.timezone.localdate", return_value=date(2026, 10, 2))
    def test_home_calendar_can_show_a_week(self, _localdate):
        response = self.client.get(
            reverse("home"),
            {"visao": "semana", "data": "2026-10-02"},
        )

        semana = response.context["semanas_calendario"][0]
        self.assertEqual(response.context["visao_calendario"], "semana")
        self.assertEqual(len(semana), 7)
        self.assertEqual(semana[0]["data"], date(2026, 9, 28))
        self.assertEqual(semana[-1]["data"], date(2026, 10, 4))
        self.assertEqual(response.context["data_anterior"], "2026-09-21")
        self.assertEqual(response.context["data_proxima"], "2026-10-05")
        self.assertContains(response, "Seg")
        self.assertContains(response, "Dom")

    @patch("core.views.timezone.localdate", return_value=date(2026, 10, 2))
    def test_home_visualization_controls_preserve_each_others_selection(self, _localdate):
        response = self.client.get(
            reverse("home"),
            {"visao": "mes", "data": "2026-10-15", "periodo": "meses"},
        )
        self.assertEqual(response.context["visao_calendario"], "mes")
        self.assertEqual(response.context["data_referencia"], date(2026, 10, 15))
        self.assertEqual(response.context["periodo"], "meses")
        self.assertContains(response, '<input type="hidden" name="periodo" value="meses">')
        self.assertContains(response, '<input type="hidden" name="visao" value="mes">')
        self.assertContains(response, '<input type="hidden" name="data" value="2026-10-15">')

    @patch("core.views.timezone.localdate", return_value=date(2026, 10, 2))
    def test_home_calendar_can_show_a_month(self, _localdate):
        response = self.client.get(
            reverse("home"),
            {"visao": "mes", "data": "2026-10-02"},
        )

        self.assertEqual(response.context["visao_calendario"], "mes")
        self.assertEqual(response.context["mes_calendario"], date(2026, 10, 1))
        self.assertEqual(len(response.context["semanas_calendario"]), 5)
        self.assertContains(response, "Outubro 2026")

    @patch("core.views.timezone.localdate", return_value=date(2026, 10, 1))
    def test_home_calendar_shows_month_appointments_and_payable_accounts(self, _localdate):
        agendamento = Agendamento.objects.create(
            data=date(2026, 10, 15),
            nome="Maria Silva",
            telefone="11999998888",
        )
        HorarioAgendado.objects.create(
            agendamento=agendamento,
            data=agendamento.data,
            agenda_key=agendamento.agenda_key,
            inicio=time(9, 0),
            fim=time(9, 30),
        )
        ContaPagar.objects.create(
            descricao="Aluguel",
            valor=Decimal("1200.00"),
            vencimento=date(2026, 10, 15),
        )
        ContaPagar.objects.create(
            descricao="Conta de novembro",
            valor=Decimal("50.00"),
            vencimento=date(2026, 11, 1),
        )

        response = self.client.get(reverse("home"), {"mes": "2026-10"})

        self.assertEqual(response.context["mes_calendario"], date(2026, 10, 1))
        dia = next(
            dia
            for semana in response.context["semanas_calendario"]
            for dia in semana
            if dia["data"] == date(2026, 10, 15)
        )
        self.assertEqual(dia["agendamentos"][0]["nome"], "Maria Silva")
        self.assertEqual(dia["agendamentos"][0]["agendar_para"], "—")
        self.assertEqual(dia["agendamentos"][0]["horarios"], "09:00")
        self.assertEqual([conta.descricao for conta in dia["contas"]], ["Aluguel"])
        self.assertContains(response, "Agenda e contas a pagar")
        self.assertContains(response, "Maria Silva")
        self.assertContains(response, "Aluguel")
        self.assertNotContains(response, "Conta de novembro")

    @patch("core.views.timezone.localdate", return_value=date(2026, 10, 1))
    def test_home_calendar_groups_overlapping_resource_schedules_together(self, _localdate):
        funcionario = Funcionario.objects.create(nome="Ana Silva", funcao="Cabeleireira")
        agendamentos = [
            Agendamento.objects.create(
                data=date(2026, 10, 15),
                nome="Cliente da Ana",
                telefone="11999998888",
                funcionario=funcionario,
            ),
            Agendamento.objects.create(
                data=date(2026, 10, 15),
                nome="Evento manual",
                telefone="11999997777",
                descricao_agendar_para="Evento",
            ),
        ]
        for agendamento in agendamentos:
            HorarioAgendado.objects.create(
                agendamento=agendamento,
                data=agendamento.data,
                agenda_key=agendamento.agenda_key,
                inicio=time(9, 0),
                fim=time(9, 30),
            )

        response = self.client.get(reverse("home"), {"mes": "2026-10"})
        dia = next(
            dia
            for semana in response.context["semanas_calendario"]
            for dia in semana
            if dia["data"] == date(2026, 10, 15)
        )

        self.assertEqual(len(dia["agendamentos"]), 2)
        self.assertCountEqual(
            [item["agendar_para"] for item in dia["agendamentos"]],
            ["Ana Silva", "Evento"],
        )
        self.assertContains(response, "Cliente da Ana")
        self.assertContains(response, "Evento manual")

    @patch("core.views.timezone.localdate", return_value=date(2026, 10, 1))
    def test_home_calendar_month_navigation_handles_year_boundaries(self, _localdate):
        response = self.client.get(reverse("home"), {"mes": "2026-12"})

        self.assertEqual(response.context["mes_calendario"], date(2026, 12, 1))
        self.assertEqual(response.context["mes_anterior"], "2026-11")
        self.assertEqual(response.context["proximo_mes"], "2027-01")

    def test_home_calendar_displays_fixed_and_movable_national_holidays(self):
        response = self.client.get(reverse("home"), {"mes": "2026-04"})

        dias = {
            dia["data"]: dia
            for semana in response.context["semanas_calendario"]
            for dia in semana
        }
        self.assertEqual(dias[date(2026, 4, 3)]["feriado"], "Paixão de Cristo")
        self.assertEqual(dias[date(2026, 4, 21)]["feriado"], "Tiradentes")
        self.assertContains(response, "Paixão de Cristo")
        self.assertContains(response, "Tiradentes")

        novembro = self.client.get(reverse("home"), {"mes": "2026-11"})
        dias_novembro = {
            dia["data"]: dia
            for semana in novembro.context["semanas_calendario"]
            for dia in semana
        }
        self.assertEqual(
            dias_novembro[date(2026, 11, 20)]["feriado"],
            "Dia Nacional de Zumbi e da Consciência Negra",
        )

    def test_home_calendar_displays_national_optional_holidays(self):
        fevereiro = self.client.get(reverse("home"), {"mes": "2026-02"})
        dias_fevereiro = {
            dia["data"]: dia
            for semana in fevereiro.context["semanas_calendario"]
            for dia in semana
        }
        self.assertEqual(
            dias_fevereiro[date(2026, 2, 16)]["ponto_facultativo"],
            "Carnaval (ponto facultativo)",
        )
        self.assertEqual(
            dias_fevereiro[date(2026, 2, 17)]["ponto_facultativo"],
            "Carnaval (ponto facultativo)",
        )
        self.assertEqual(
            dias_fevereiro[date(2026, 2, 18)]["ponto_facultativo"],
            "Quarta-feira de Cinzas (ponto facultativo até 14h)",
        )
        self.assertContains(fevereiro, "Ponto facultativo")

        junho = self.client.get(reverse("home"), {"mes": "2026-06"})
        dias_junho = {
            dia["data"]: dia
            for semana in junho.context["semanas_calendario"]
            for dia in semana
        }
        self.assertEqual(
            dias_junho[date(2026, 6, 4)]["ponto_facultativo"],
            "Corpus Christi (ponto facultativo)",
        )

    def test_dashboard_chart_initialization_is_independent_of_tooltips(self):
        response = self.client.get(reverse("home"))
        conteudo = response.content.decode()

        self.assertLess(
            conteudo.index('new Chart(document.getElementById("caixa-chart")'),
            conteudo.index("if (window.bootstrap && window.bootstrap.Tooltip)"),
        )
        self.assertContains(response, 'id="produtos-chart"')
        self.assertContains(response, 'id="servicos-chart"')
        self.assertContains(response, 'id="pagamentos-chart"')
        self.assertContains(response, 'id="estoque-chart"')
        self.assertContains(response, 'id="caixa-chart"')

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
        Cliente.objects.create(
            nome="Ana Souza",
            cpf="52998224725",
            telefone="11999998888",
        )

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_vendas_hoje"], Decimal("150.00"))
        self.assertEqual(response.context["vendas_hoje"], 2)
        self.assertEqual(response.context["total_clientes"], 1)
        self.assertEqual(
            [
                (item["descricao"], item["quantidade"])
                for item in response.context["produtos_mais_vendidos_hoje"]
            ],
            [("Shampoo", 4), ("Condicionador", 2)],
        )
        self.assertEqual(
            [
                (item["forma"], item["total"])
                for item in response.context["formas_pagamento_hoje"]
            ],
            [("Pix", Decimal("100.00")), ("Dinheiro", Decimal("50.00"))],
        )
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
        self.assertContains(response, "Home")
        self.assertContains(response, "Quinta-feira, 01/10/2026")
        self.assertContains(response, "Agenda e contas a pagar.")
        self.assertContains(response, "Vendas hoje")
        self.assertContains(response, "Nº de vendas")
        self.assertContains(response, "Carteira de Clientes")
        self.assertContains(response, "Produtos mais vendidos hoje")
        self.assertContains(response, "Formas de pagamento (hoje)")
        self.assertContains(response, "Repor estoque (abaixo de 5 un.)")
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
    def test_daily_dashboard_indicators_exclude_other_days_and_handle_zero_payments(
        self,
        _localdate,
    ):
        self.criar_venda(
            date(2026, 9, 30),
            Venda.FormaPagamento.DINHEIRO,
            "150.00",
            [(ItemVenda.Tipo.PRODUTO, "Produto de ontem", 2)],
        )
        self.criar_venda(date(2026, 10, 1), Venda.FormaPagamento.PIX, "0.00")

        response = self.client.get(reverse("home"))

        self.assertEqual(response.context["total_vendas_hoje"], Decimal("0.00"))
        self.assertEqual(response.context["vendas_hoje"], 1)
        self.assertEqual(response.context["produtos_mais_vendidos_hoje"], [])
        self.assertEqual(
            response.context["formas_pagamento_hoje"],
            [{"forma": "Pix", "total": Decimal("0.00"), "percentual": 0}],
        )

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
        self.assertContains(
            hoje_response,
            "Produto: Shampoo × 1 — R$ 120,50 cada (R$ 120,50)",
        )
        self.assertContains(hoje_response, "font-size: 7.5pt")
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
        self.assertContains(response, "font-size: 7.5pt")

    def test_reports_are_available_from_navigation(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, reverse("relatorio_caixa"))
        self.assertContains(response, reverse("relatorio_estoque"))
