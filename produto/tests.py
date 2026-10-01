from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Produto


class ProdutoCRUDTests(TestCase):
    def setUp(self):
        self.produto = Produto.objects.create(
            descricao="Shampoo",
            preco_custo="12.50",
            preco_venda="25.00",
            quantidade=10,
            despesas_variaveis_percentual="10.00",
            lucro_desejado_percentual="20.00",
        )

    def test_create_produto(self):
        response = self.client.post(
            reverse("criar_produto"),
            {
                "descricao": "Condicionador",
                "preco_custo": "15.00",
                "despesas_variaveis_percentual": "10.00",
                "lucro_desejado_percentual": "20.00",
                "quantidade": 8,
            },
        )

        self.assertRedirects(response, reverse("listar_produto"))
        produto = Produto.objects.get(descricao="Condicionador")
        self.assertEqual(str(produto.preco_venda), "21.43")

    def test_create_produto_preserves_user_selected_price(self):
        response = self.client.post(
            reverse("criar_produto"),
            {
                "descricao": "Condicionador",
                "preco_custo": "15.00",
                "despesas_variaveis_percentual": "10.00",
                "lucro_desejado_percentual": "20.00",
                "preco_venda": "25.00",
                "quantidade": 8,
            },
        )

        self.assertRedirects(response, reverse("listar_produto"))
        produto = Produto.objects.get(descricao="Condicionador")
        self.assertEqual(str(produto.preco_venda), "25.00")

    def test_invalid_product_data_is_not_saved(self):
        response = self.client.post(
            reverse("criar_produto"),
            {
                "descricao": "Condicionador",
                "preco_custo": "inválido",
                "despesas_variaveis_percentual": "10.00",
                "lucro_desejado_percentual": "20.00",
                "quantidade": 8,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["preco_custo"])
        self.assertEqual(Produto.objects.count(), 1)

    def test_edit_produto(self):
        response = self.client.post(
            reverse("editar_produto", args=[self.produto.pk]),
            {
                "descricao": "Shampoo profissional",
                "preco_custo": "14.00",
                "despesas_variaveis_percentual": "10.00",
                "lucro_desejado_percentual": "20.00",
                "quantidade": 12,
            },
        )

        self.assertRedirects(response, reverse("listar_produto"))
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.descricao, "Shampoo profissional")
        self.assertEqual(str(self.produto.preco_custo), "14.00")
        self.assertEqual(str(self.produto.preco_venda), "20.00")
        self.assertEqual(self.produto.quantidade, 12)

    def test_delete_requires_post_confirmation(self):
        confirmation = self.client.get(
            reverse("excluir_produto", args=[self.produto.pk])
        )
        self.assertEqual(confirmation.status_code, 200)
        self.assertTrue(Produto.objects.filter(pk=self.produto.pk).exists())

        response = self.client.post(
            reverse("excluir_produto", args=[self.produto.pk])
        )

        self.assertRedirects(response, reverse("listar_produto"))
        self.assertFalse(Produto.objects.filter(pk=self.produto.pk).exists())

    def test_list_can_be_filtered_by_description(self):
        response = self.client.get(reverse("listar_produto"), {"q": "shamp"})

        self.assertContains(response, "Shampoo")
        self.assertNotContains(response, "Condicionador")

    def test_price_fields_are_displayed_as_brazilian_currency(self):
        response = self.client.get(reverse("listar_produto"))

        self.assertContains(response, "R$ 12,50")
        self.assertContains(response, "R$ 25,00")

    def test_list_calculates_net_profit_and_stock_totals(self):
        Produto.objects.create(
            descricao="Condicionador",
            preco_custo="15.00",
            preco_venda="30.00",
            quantidade=8,
            despesas_variaveis_percentual="10.00",
            lucro_desejado_percentual="20.00",
        )

        response = self.client.get(reverse("listar_produto"))

        self.assertEqual(response.context["quantidade_total"], 18)
        self.assertEqual(response.context["valor_estoque_total"], Decimal("490.00"))
        self.assertEqual(response.context["lucro_estoque_total"], Decimal("196.00"))
        self.assertContains(response, "R$ 10,00")
        self.assertContains(response, "R$ 12,00")
        self.assertContains(response, "R$ 250,00")
        self.assertContains(response, "R$ 240,00")

    def test_product_table_headers_have_hover_explanations(self):
        response = self.client.get(reverse("listar_produto"))

        for explanation in (
            "Identificador único do produto",
            "Valor pago para adquirir ou produzir",
            "Percentual de impostos, taxas",
            "Percentual de lucro líquido desejado",
            "Preço final de venda definido",
            "Preço de venda menos custo direto",
            "Número de unidades disponíveis",
            "Valor total das unidades em estoque",
            "Lucro líquido estimado se todas",
            "Ações disponíveis para este produto",
        ):
            with self.subTest(explanation=explanation):
                self.assertContains(response, explanation)

    def test_product_table_centers_numeric_columns(self):
        response = self.client.get(reverse("listar_produto"))

        self.assertContains(response, '<th scope="col" class="text-center"', count=9)
        self.assertContains(response, '<td class="text-center">R$ 12,50</td>')
        self.assertContains(response, '<td class="text-center">10</td>')

    def test_products_without_expense_percent_are_excluded_from_profit_total(self):
        Produto.objects.create(
            descricao="Escova",
            preco_custo="5.00",
            preco_venda="10.00",
            quantidade=2,
        )

        response = self.client.get(reverse("listar_produto"))

        self.assertEqual(response.context["produtos_sem_despesas_cadastradas"], 1)
        self.assertEqual(response.context["lucro_estoque_total"], Decimal("100.00"))
        self.assertContains(response, "sem percentual de despesas variáveis cadastrado")

    def test_product_form_shows_currency_prefix_for_price_fields(self):
        response = self.client.get(reverse("criar_produto"))

        self.assertContains(response, '<span class="input-group-text">R$</span>', count=2)
        self.assertContains(response, "title=\"Valor pago para adquirir ou produzir")
        self.assertContains(response, "title=\"Impostos, taxas, comissões")
        self.assertContains(response, "title=\"Sugestão calculada pelo markup")
        self.assertNotContains(response, 'id="id_preco_venda" disabled')

    def test_markup_percentages_must_total_less_than_100(self):
        response = self.client.post(
            reverse("criar_produto"),
            {
                "descricao": "Condicionador",
                "preco_custo": "15.00",
                "despesas_variaveis_percentual": "60.00",
                "lucro_desejado_percentual": "40.00",
                "quantidade": 8,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["lucro_desejado_percentual"])
        self.assertEqual(Produto.objects.count(), 1)

    def test_list_can_be_filtered_by_price(self):
        Produto.objects.create(
            descricao="Condicionador",
            preco_custo="15.00",
            preco_venda="30.00",
            quantidade=8,
        )

        response = self.client.get(reverse("listar_produto"), {"q": "30,00"})

        self.assertContains(response, "Condicionador")
        self.assertNotContains(response, "Shampoo")

    def test_list_can_be_filtered_by_quantity(self):
        Produto.objects.create(
            descricao="Condicionador",
            preco_custo="15.00",
            preco_venda="30.00",
            quantidade=8,
        )

        response = self.client.get(reverse("listar_produto"), {"q": "8"})

        self.assertContains(response, "Condicionador")
        self.assertNotContains(response, "Shampoo")

    def test_list_can_be_sorted_by_description_ascending_or_descending(self):
        Produto.objects.create(
            descricao="Acondicionador",
            preco_custo="10.00",
            preco_venda="20.00",
            quantidade=5,
        )

        ascending = self.client.get(
            reverse("listar_produto"), {"ordenar": "descricao_asc"}
        )
        descending = self.client.get(
            reverse("listar_produto"), {"ordenar": "descricao_desc"}
        )

        self.assertEqual(
            [produto.descricao for produto in ascending.context["produtos"]],
            ["Acondicionador", "Shampoo"],
        )
        self.assertEqual(
            [produto.descricao for produto in descending.context["produtos"]],
            ["Shampoo", "Acondicionador"],
        )

    def test_list_can_be_sorted_by_quantity_ascending_or_descending(self):
        Produto.objects.create(
            descricao="Condicionador",
            preco_custo="15.00",
            preco_venda="30.00",
            quantidade=8,
        )

        ascending = self.client.get(
            reverse("listar_produto"), {"ordenar": "quantidade_asc"}
        )
        descending = self.client.get(
            reverse("listar_produto"), {"ordenar": "quantidade_desc"}
        )

        self.assertEqual(
            [produto.quantidade for produto in ascending.context["produtos"]],
            [8, 10],
        )
        self.assertEqual(
            [produto.quantidade for produto in descending.context["produtos"]],
            [10, 8],
        )

    def test_invalid_sort_option_uses_description_ascending(self):
        response = self.client.get(
            reverse("listar_produto"), {"ordenar": "campo_inexistente"}
        )

        self.assertEqual(response.context["ordenar"], "descricao_asc")
