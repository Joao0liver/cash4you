from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import ContaPagar, Funcionario


class ContaPagarTests(TestCase):
    def test_create_and_list_employee(self):
        response = self.client.post(
            reverse("criar_funcionario"),
            {"nome": "Ana Silva", "funcao": "Gerente"},
        )

        self.assertRedirects(response, reverse("listar_funcionarios"))
        funcionario = Funcionario.objects.get()
        self.assertEqual(funcionario.nome, "Ana Silva")
        self.assertEqual(funcionario.funcao, "Gerente")

        listing = self.client.get(reverse("listar_funcionarios"))
        self.assertContains(listing, "Funcionários")
        self.assertContains(listing, "Ana Silva")
        self.assertContains(listing, "Gerente")

    def test_employee_pages_are_nested_in_registration_navigation(self):
        response = self.client.get(reverse("listar_funcionarios"))

        self.assertContains(
            response,
            f'<a href="{reverse("listar_funcionarios")}" class="nav-link active">',
        )
        self.assertContains(
            response,
            'data-nav-paths="/cadastrar/,/produto/,/servico/,/cliente/,/contas-a-pagar/funcionarios/,/contas-a-pagar/" aria-label="Abrir menu Cadastrar"',
        )
        self.assertContains(response, "Funcionários")
        self.assertNotContains(
            response,
            f'<a href="{reverse("listar_contas_pagar")}" class="nav-link active">',
        )

    def test_employee_name_and_role_are_required(self):
        response = self.client.post(
            reverse("criar_funcionario"),
            {"nome": "", "funcao": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("nome", response.context["form"].errors)
        self.assertIn("funcao", response.context["form"].errors)
        self.assertFalse(Funcionario.objects.exists())

    def test_create_and_list_payable_account(self):
        response = self.client.post(
            reverse("criar_conta_pagar"),
            {
                "descricao": "Aluguel",
                "valor": "1200.00",
                "vencimento": "2026-10-10",
            },
        )

        self.assertRedirects(response, reverse("listar_contas_pagar"))
        conta = ContaPagar.objects.get()
        self.assertEqual(conta.descricao, "Aluguel")
        self.assertEqual(conta.valor, Decimal("1200.00"))
        self.assertEqual(conta.vencimento, date(2026, 10, 10))
        self.assertFalse(conta.paga)

        listing = self.client.get(reverse("listar_contas_pagar"))
        self.assertContains(listing, "Aluguel")
        self.assertContains(listing, "Pendente")

    def test_invalid_payable_amount_is_rejected(self):
        response = self.client.post(
            reverse("criar_conta_pagar"),
            {
                "descricao": "Conta inválida",
                "valor": "-1.00",
                "vencimento": "2026-10-10",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("valor", response.context["form"].errors)
        self.assertFalse(ContaPagar.objects.exists())

    def test_edit_toggle_paid_status_and_delete(self):
        conta = ContaPagar.objects.create(
            descricao="Energia",
            valor=Decimal("80.00"),
            vencimento=date(2026, 10, 12),
        )
        update = self.client.post(
            reverse("editar_conta_pagar", args=[conta.pk]),
            {
                "descricao": "Energia elétrica",
                "valor": "85.00",
                "vencimento": "2026-10-13",
                "paga": "on",
            },
        )
        self.assertRedirects(update, reverse("listar_contas_pagar"))
        conta.refresh_from_db()
        self.assertEqual(conta.descricao, "Energia elétrica")
        self.assertEqual(conta.valor, Decimal("85.00"))
        self.assertTrue(conta.paga)

        toggle = self.client.post(
            reverse("alternar_status_conta", args=[conta.pk])
        )
        self.assertRedirects(toggle, reverse("listar_contas_pagar"))
        conta.refresh_from_db()
        self.assertFalse(conta.paga)

        confirmation = self.client.get(
            reverse("excluir_conta_pagar", args=[conta.pk])
        )
        self.assertEqual(confirmation.status_code, 200)
        deleted = self.client.post(
            reverse("excluir_conta_pagar", args=[conta.pk])
        )
        self.assertRedirects(deleted, reverse("listar_contas_pagar"))
        self.assertFalse(ContaPagar.objects.exists())
