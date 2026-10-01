from django.test import TestCase
from django.urls import reverse

from .models import Servico


class ServicoCRUDTests(TestCase):
    def setUp(self):
        self.servico = Servico.objects.create(
            descricao="Corte de cabelo",
            preco_venda="45.00",
        )

    def test_create_servico(self):
        response = self.client.post(
            reverse("criar_servico"),
            {
                "descricao": "Coloração",
                "custo_direto": "80.00",
                "despesas_variaveis_percentual": "10.00",
                "lucro_desejado_percentual": "20.00",
            },
        )

        self.assertRedirects(response, reverse("listar_servico"))
        servico = Servico.objects.get(descricao="Coloração")
        self.assertEqual(str(servico.preco_venda), "114.29")

    def test_create_servico_preserves_user_selected_price(self):
        response = self.client.post(
            reverse("criar_servico"),
            {
                "descricao": "Coloração",
                "custo_direto": "80.00",
                "despesas_variaveis_percentual": "10.00",
                "lucro_desejado_percentual": "20.00",
                "preco_venda": "125.00",
            },
        )

        self.assertRedirects(response, reverse("listar_servico"))
        servico = Servico.objects.get(descricao="Coloração")
        self.assertEqual(str(servico.preco_venda), "125.00")

    def test_invalid_price_is_not_saved(self):
        response = self.client.post(
            reverse("criar_servico"),
            {
                "descricao": "Coloração",
                "custo_direto": "inválido",
                "despesas_variaveis_percentual": "10.00",
                "lucro_desejado_percentual": "20.00",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["custo_direto"])
        self.assertEqual(Servico.objects.count(), 1)

    def test_edit_servico(self):
        response = self.client.post(
            reverse("editar_servico", args=[self.servico.pk]),
            {
                "descricao": "Corte e escova",
                "custo_direto": "40.00",
                "despesas_variaveis_percentual": "10.00",
                "lucro_desejado_percentual": "20.00",
            },
        )

        self.assertRedirects(response, reverse("listar_servico"))
        self.servico.refresh_from_db()
        self.assertEqual(self.servico.descricao, "Corte e escova")
        self.assertEqual(str(self.servico.custo_direto), "40.00")
        self.assertEqual(str(self.servico.preco_venda), "57.14")

    def test_delete_requires_post_confirmation(self):
        confirmation = self.client.get(
            reverse("excluir_servico", args=[self.servico.pk])
        )
        self.assertEqual(confirmation.status_code, 200)
        self.assertTrue(Servico.objects.filter(pk=self.servico.pk).exists())

        response = self.client.post(
            reverse("excluir_servico", args=[self.servico.pk])
        )

        self.assertRedirects(response, reverse("listar_servico"))
        self.assertFalse(Servico.objects.filter(pk=self.servico.pk).exists())

    def test_list_can_be_filtered_by_description(self):
        response = self.client.get(reverse("listar_servico"), {"q": "corte"})

        self.assertContains(response, "Corte de cabelo")
        self.assertNotContains(response, "Coloração")

    def test_price_is_displayed_as_brazilian_currency(self):
        response = self.client.get(reverse("listar_servico"))

        self.assertContains(response, "R$ 45,00")

    def test_service_table_centers_numeric_columns(self):
        response = self.client.get(reverse("listar_servico"))

        for heading, description in (
            ("Código", "Identificador único do serviço no sistema."),
            (
                "Custo direto",
                "Valor dos materiais, insumos e demais custos diretos para realizar o serviço.",
            ),
            (
                "Despesas variáveis",
                "Percentual de impostos, taxas, comissões e outras despesas variáveis sobre o preço de venda.",
            ),
            (
                "Lucro desejado",
                "Percentual de lucro líquido desejado usado como referência na precificação.",
            ),
            (
                "Preço de venda",
                "Preço final de venda definido para a realização do serviço.",
            ),
        ):
            self.assertContains(
                response,
                f'<th scope="col" class="text-center" title="{description}">{heading}</th>',
            )
        self.assertContains(response, '<td class="text-center">')
        self.assertContains(response, '<td class="text-center">R$ 45,00</td>')
        self.assertContains(response, '<td class="text-end">')

    def test_service_table_headers_explain_each_field(self):
        response = self.client.get(reverse("listar_servico"))

        for description in (
            "Identificador único do serviço no sistema.",
            "Nome usado para identificar o serviço.",
            "Valor dos materiais, insumos e demais custos diretos para realizar o serviço.",
            "Percentual de impostos, taxas, comissões e outras despesas variáveis sobre o preço de venda.",
            "Percentual de lucro líquido desejado usado como referência na precificação.",
            "Preço final de venda definido para a realização do serviço.",
            "Ações disponíveis para este serviço.",
        ):
            self.assertContains(response, f'title="{description}"')

    def test_list_displays_net_profit_for_each_service(self):
        Servico.objects.create(
            descricao="Coloração",
            custo_direto="80.00",
            despesas_variaveis_percentual="10.00",
            lucro_desejado_percentual="20.00",
            preco_venda="125.00",
        )

        response = self.client.get(reverse("listar_servico"))

        self.assertContains(response, "R$ 32,50")
        self.assertContains(
            response,
            "Preço de venda menos custo direto e despesas variáveis, por realização do serviço.",
        )

    def test_net_profit_is_not_calculated_when_cost_or_expenses_are_missing(self):
        Servico.objects.create(
            descricao="Massagem",
            custo_direto="30.00",
            despesas_variaveis_percentual=None,
            preco_venda="100.00",
        )

        response = self.client.get(reverse("listar_servico"))
        servicos = response.context["servicos"]

        self.assertIsNone(servicos[0].lucro_liquido)
        self.assertContains(response, "—")
        self.assertEqual(response.context["servicos_sem_dados_para_lucro"], 2)
        self.assertContains(
            response,
            "O lucro não foi calculado para 2 serviço(s) sem custo direto ou percentual de despesas variáveis cadastrado.",
        )

    def test_service_form_shows_currency_prefix_for_price(self):
        response = self.client.get(reverse("criar_servico"))

        self.assertContains(response, '<span class="input-group-text">R$</span>')
        self.assertContains(response, "title=\"Nome que identifica o serviço.\"")
        self.assertContains(response, "title=\"Valor dos materiais")
        self.assertContains(response, "title=\"Impostos, taxas, comissões")
        self.assertContains(response, "title=\"Sugestão calculada pelo markup")
        self.assertNotContains(response, 'id="id_preco_venda" disabled')

    def test_markup_percentages_must_total_less_than_100(self):
        response = self.client.post(
            reverse("criar_servico"),
            {
                "descricao": "Coloração",
                "custo_direto": "80.00",
                "despesas_variaveis_percentual": "60.00",
                "lucro_desejado_percentual": "40.00",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["lucro_desejado_percentual"])
        self.assertEqual(Servico.objects.count(), 1)

    def test_list_can_be_filtered_by_price(self):
        Servico.objects.create(descricao="Coloração", preco_venda="120.50")

        response = self.client.get(reverse("listar_servico"), {"q": "120,50"})

        self.assertContains(response, "Coloração")
        self.assertNotContains(response, "Corte de cabelo")

    def test_list_can_be_sorted_by_description_ascending_or_descending(self):
        Servico.objects.create(descricao="Barba", preco_venda="25.00")

        ascending = self.client.get(
            reverse("listar_servico"), {"ordenar": "descricao_asc"}
        )
        descending = self.client.get(
            reverse("listar_servico"), {"ordenar": "descricao_desc"}
        )

        self.assertEqual(
            list(ascending.context["servicos"].values_list("descricao", flat=True)),
            ["Barba", "Corte de cabelo"],
        )
        self.assertEqual(
            list(descending.context["servicos"].values_list("descricao", flat=True)),
            ["Corte de cabelo", "Barba"],
        )

    def test_invalid_sort_option_uses_description_ascending(self):
        response = self.client.get(
            reverse("listar_servico"), {"ordenar": "campo_inexistente"}
        )

        self.assertEqual(response.context["ordenar"], "descricao_asc")
