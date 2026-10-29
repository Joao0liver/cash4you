from datetime import date, datetime, time
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalogo.models import Produto, Servico
from configuracao.models import DadosEstabelecimento
from vendaitem.models import VendaItem
from .models import PagamentoVenda, Venda


class CaixaTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.usuario = User.objects.create_superuser(
            email="testes@cash4you.local",
            nome="Usuário de Teste",
            password="senha-teste-123",
        )

    def setUp(self):
        self.client.force_login(self.usuario)
        self.produto = Produto.objects.create(
            descricao="Shampoo",
            preco_custo=Decimal("10.00"),
            preco_venda=Decimal("25.00"),
            quantidade=5,
        )
        self.servico = Servico.objects.create(
            descricao="Corte",
            preco_venda=Decimal("40.00"),
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

    def criar_venda(self, total=Decimal("25.00"), nome_cliente="Cliente Teste",
                    telefone_whatsapp=""):
        venda = Venda.objects.create(
            nome_cliente=nome_cliente,
            telefone_whatsapp=telefone_whatsapp,
            total=total,
        )
        PagamentoVenda.objects.create(
            venda=venda,
            forma_pagamento=PagamentoVenda.FormaPagamento.PIX,
            valor=total,
            valor_recebido=total,
            troco=Decimal("0.00"),
        )
        return venda

    def criar_item_venda(self, venda, item, quantidade=1):
        return VendaItem.objects.create(
            venda=venda,
            item=item,
            quantidade=quantidade,
            valor_unitario=item.preco_venda,
        )

    def test_caixa_exibe_produtos_servicos_e_carrinho(self):
        response = self.client.get(reverse("caixa"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Shampoo")
        self.assertContains(response, "Corte")
        self.assertContains(response, "Carrinho")
        self.assertContains(response, "Buscar produto")
        self.assertContains(response, "Buscar serviço")
        self.assertContains(response, "Últimas vendas")
        self.assertContains(response, "Ainda não há vendas registradas.")

    def test_caixa_exibe_apenas_tres_vendas_mais_recentes(self):
        vendas = []
        for indice in range(4):
            venda = self.criar_venda(
                nome_cliente=f"Cliente {indice}",
            )
            self.criar_item_venda(venda, self.produto)
            vendas.append(venda)

        response = self.client.get(reverse("caixa"))

        self.assertEqual(
            list(response.context["vendas_recentes"]),
            list(reversed(vendas[-3:])),
        )
        self.assertNotContains(response, "Cliente 0")
        for venda in vendas[-3:]:
            self.assertContains(response, f"Venda #{venda.pk}")

    def test_adiciona_produto_e_servico_e_atualiza_quantidade(self):
        self.adicionar("produto", self.produto)
        self.adicionar("servico", self.servico)

        chave_produto = f"produto:{self.produto.pk}"
        response = self.client.post(
            reverse("caixa"),
            {
                "acao": "atualizar",
                "chave": chave_produto,
                "quantidade": "2",
            },
        )

        self.assertRedirects(response, reverse("caixa"))
        self.assertEqual(self.client.session["venda_cart"][chave_produto], 2)

        response = self.client.get(reverse("caixa"))
        self.assertContains(response, "R$ 90,00")

    def test_remove_item_do_carrinho(self):
        self.adicionar("produto", self.produto)

        response = self.client.post(
            reverse("caixa"),
            {"acao": "remover", "chave": f"produto:{self.produto.pk}"},
        )

        self.assertRedirects(response, reverse("caixa"))
        self.assertEqual(self.client.session.get("venda_cart", {}), {})

    def test_venda_em_dinheiro_calcula_troco_e_reduz_estoque(self):
        self.adicionar("produto", self.produto)

        response = self.finalizar(
            forma_pagamento="dinheiro",
            valor_recebido="30,50",
            telefone_whatsapp="(11) 99999-8888",
            nome_cliente="Ana Souza",
        )

        venda = Venda.objects.get()
        pagamento = venda.pagamentos.get()

        self.assertRedirects(
            response,
            reverse("detalhe_venda", kwargs={"id": venda.pk}),
        )
        self.assertEqual(venda.total, Decimal("25.00"))
        self.assertEqual(venda.nome_cliente, "Ana Souza")
        self.assertEqual(venda.telefone_whatsapp, "11999998888")
        self.assertEqual(pagamento.valor, Decimal("25.00"))
        self.assertEqual(pagamento.valor_recebido, Decimal("30.50"))
        self.assertEqual(pagamento.troco, Decimal("5.50"))

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 4)
        item_vendido = venda.itens.get()
        self.assertEqual(item_vendido.item.descricao, self.produto.descricao)
        self.assertEqual(item_vendido.quantidade, 1)
        self.assertEqual(item_vendido.valor_unitario, Decimal("25.00"),)

    def test_venda_com_produto_e_servico_baixa_estoque_apenas_do_produto(self):
        self.adicionar("produto", self.produto)
        self.adicionar("servico", self.servico)
        self.client.post(
            reverse("caixa"),
            {
                "acao": "atualizar",
                "chave": f"servico:{self.servico.pk}",
                "quantidade": "2",
            },
        )

        response = self.finalizar(telefone_whatsapp="11999998888")
        venda = Venda.objects.get()

        self.assertRedirects(
            response,
            reverse("detalhe_venda", kwargs={"id": venda.pk}),
        )
        self.assertEqual(venda.total, Decimal("105.00"))
        self.assertEqual(venda.itens.count(), 2)

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 4)
        item_servico = venda.itens.get(item=self.servico)
        self.assertEqual(item_servico.quantidade, 2)
        self.assertEqual(item_servico.valor_unitario, Decimal("40.00"))

    def test_cartao_e_pix_nao_exigem_valor_recebido_em_dinheiro(self):
        for forma in ("credito", "debito", "pix"):
            with self.subTest(forma_pagamento=forma):
                self.adicionar("servico", self.servico)
                response = self.finalizar(forma_pagamento=forma)
                self.assertEqual(response.status_code, 302)

                venda = Venda.objects.latest("pk")
                pagamento = venda.pagamentos.get()
                self.assertEqual(pagamento.forma_pagamento, forma)
                self.assertEqual(pagamento.valor, Decimal("40.00"))
                self.assertEqual(pagamento.troco, Decimal("0.00"))

    def test_pagamento_em_dinheiro_insuficiente_nao_cria_venda_nem_baixa_estoque(self):
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

    def test_estoque_insuficiente_impede_finalizacao_e_preserva_carrinho(self):
        self.adicionar("produto", self.produto)
        Produto.objects.filter(pk=self.produto.pk).update(quantidade=0)

        response = self.finalizar()

        self.assertRedirects(response, reverse("caixa"))
        self.assertEqual(Venda.objects.count(), 0)
        self.assertTrue(self.client.session["venda_cart"])

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 0)

    def test_quantidade_no_carrinho_nao_pode_exceder_estoque(self):
        self.adicionar("produto", self.produto)

        response = self.client.post(
            reverse("caixa"),
            {
                "acao": "atualizar",
                "chave": f"produto:{self.produto.pk}",
                "quantidade": "6",
            },
        )

        self.assertRedirects(response, reverse("caixa"))
        self.assertEqual(
            self.client.session["venda_cart"][f"produto:{self.produto.pk}"],
            1,
        )

    def test_detalhe_da_venda_exibe_link_do_whatsapp(self):
        self.adicionar("produto", self.produto)
        self.finalizar(
            telefone_whatsapp="11999998888",
            nome_cliente="Ana Souza",
        )
        venda = Venda.objects.get()

        response = self.client.get(
            reverse("detalhe_venda", kwargs={"id": venda.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Abrir resumo no WhatsApp")
        self.assertContains(response, "Shampoo")
        self.assertIn("wa.me/5511999998888", response.context["whatsapp_url"])

        mensagem = parse_qs(
            urlparse(response.context["whatsapp_url"]).query
        )["text"][0]
        self.assertIn("Olá Ana Souza,", mensagem)
        self.assertIn("Shampoo x 1", mensagem)
        self.assertIn("Valor total: R$ 25,00", mensagem)

    def test_venda_sem_telefone_nao_exibe_link_do_whatsapp(self):
        self.adicionar("produto", self.produto)
        self.finalizar()
        venda = Venda.objects.get()

        response = self.client.get(
            reverse("detalhe_venda", kwargs={"id": venda.pk})
        )

        self.assertContains(response, "Nenhum telefone foi informado")
        self.assertNotContains(response, "wa.me/")

    def test_historico_lista_vendas_concluidas(self):
        venda = self.criar_venda()
        self.criar_item_venda(venda, self.produto)

        response = self.client.get(reverse("listar_vendas"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Registro de Vendas")
        self.assertContains(response, "R$ 25,00")

    def test_historico_filtra_por_forma_de_pagamento_e_intervalo_de_datas(self):
        vendas = []
        for dia, forma in (
            (date(2026, 10, 1), PagamentoVenda.FormaPagamento.PIX),
            (date(2026, 10, 2), PagamentoVenda.FormaPagamento.DINHEIRO),
            (date(2026, 10, 3), PagamentoVenda.FormaPagamento.CREDITO),
            (date(2026, 10, 2), PagamentoVenda.FormaPagamento.DEBITO),
        ):
            venda = self.criar_venda()
            pagamento = venda.pagamentos.get()
            pagamento.forma_pagamento = forma
            pagamento.save()
            instante = timezone.make_aware(
                datetime.combine(dia, time(12, 0)),
                timezone.get_current_timezone(),
            )
            Venda.objects.filter(pk=venda.pk).update(criada_em=instante)
            vendas.append(venda)

        response = self.client.get(
            reverse("listar_vendas"),
            [
                ("pagamentos", PagamentoVenda.FormaPagamento.DINHEIRO),
                ("pagamentos", PagamentoVenda.FormaPagamento.PIX),
                ("data_inicial", "2026-10-01"),
                ("data_final", "2026-10-02"),
            ],
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {v.pk for v in response.context["vendas"]},
            {vendas[0].pk, vendas[1].pk},
        )
        self.assertTrue(response.context["form_filtro"].is_valid())

    def test_historico_rejeita_data_final_anterior_a_data_inicial(self):
        response = self.client.get(
            reverse("listar_vendas"),
            {"data_inicial": "2026-10-03", "data_final": "2026-10-01"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form_filtro"].is_valid())
        self.assertContains(
            response,
            "A data final deve ser igual ou posterior à data inicial.",
        )

    def test_editar_venda_atualiza_total_itens_e_estoque(self):
        self.adicionar("produto", self.produto)
        self.finalizar(telefone_whatsapp="11999998888")
        venda = Venda.objects.get()

        response = self.client.get(
            reverse("editar_venda", kwargs={"id": venda.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Editar venda")

        response = self.client.post(
            reverse("editar_venda", kwargs={"id": venda.pk}),
            {
                "forma_pagamento": "dinheiro",
                "valor_recebido": "60.00",
                "telefone_whatsapp": "11999997777",
                "nome_cliente": "Cliente Editado",
                f"produto_{self.produto.pk}": "2",
                f"servico_{self.servico.pk}": "0",
            },
        )

        self.assertRedirects(
            response,
            reverse("detalhe_venda", kwargs={"id": venda.pk}),
        )
        venda.refresh_from_db()
        self.produto.refresh_from_db()
        self.assertEqual(venda.total, Decimal("50.00"))
        self.assertEqual(venda.telefone_whatsapp, "11999997777")
        self.assertEqual(venda.nome_cliente, "Cliente Editado")
        self.assertEqual(venda.itens.get().quantidade, 2)
        self.assertEqual(self.produto.quantidade, 3)

    def test_excluir_venda_restaura_estoque_do_produto(self):
        self.adicionar("produto", self.produto)
        self.finalizar()
        venda = Venda.objects.get()

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 4)

        response = self.client.post(
            reverse("excluir_venda", kwargs={"id": venda.pk})
        )

        self.assertRedirects(response, reverse("listar_vendas"))
        self.assertFalse(Venda.objects.filter(pk=venda.pk).exists())

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 5)
