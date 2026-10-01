from django.test import TestCase
from django.core.exceptions import ValidationError
from django.urls import reverse

from .models import Cliente


class ClienteCPFValidationTests(TestCase):
    def make_cliente(self, cpf):
        return Cliente(nome="Maria Silva", cpf=cpf, telefone="11999999999")

    def test_accepts_valid_cpf(self):
        self.make_cliente("52998224725").full_clean()

    def test_rejects_cpf_with_invalid_check_digits(self):
        cliente = self.make_cliente("52998224724")

        with self.assertRaises(ValidationError) as error:
            cliente.full_clean()

        self.assertIn("cpf", error.exception.message_dict)

    def test_rejects_cpf_with_repeated_digits(self):
        cliente = self.make_cliente("11111111111")

        with self.assertRaises(ValidationError) as error:
            cliente.full_clean()

        self.assertIn("cpf", error.exception.message_dict)


class ClienteActionsTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nome="Maria Silva",
            cpf="52998224725",
            telefone="11999999999",
        )

    def test_create_cliente(self):
        response = self.client.post(
            reverse("criar_cliente"),
            {"nome": "Joao Souza", "cpf": "11144477735", "telefone": "11988887777"},
        )

        self.assertRedirects(response, reverse("listar_cliente"))
        self.assertTrue(Cliente.objects.filter(cpf="11144477735").exists())

    def test_cliente_form_includes_live_cpf_validation(self):
        response = self.client.get(reverse("criar_cliente"))

        self.assertContains(response, 'id="cpf-feedback"')
        self.assertContains(response, 'cpfInput.addEventListener("input"')
        self.assertContains(response, "CPF inválido. Confira os números digitados.")

    def test_phone_number_links_to_whatsapp(self):
        response = self.client.get(reverse("listar_cliente"))

        self.assertContains(
            response,
            'href="https://wa.me/5511999999999"',
        )

    def test_list_can_be_filtered_by_name(self):
        response = self.client.get(reverse("listar_cliente"), {"q": "maria"})

        self.assertContains(response, "Maria Silva")
        self.assertNotContains(response, "João Souza")

    def test_list_can_be_filtered_by_cpf_with_punctuation(self):
        Cliente.objects.create(
            nome="João Souza",
            cpf="11144477735",
            telefone="11988887777",
        )

        response = self.client.get(reverse("listar_cliente"), {"q": "111.444"})

        self.assertContains(response, "João Souza")
        self.assertNotContains(response, "Maria Silva")

    def test_list_can_be_filtered_by_phone(self):
        Cliente.objects.create(
            nome="João Souza",
            cpf="11144477735",
            telefone="11988887777",
        )

        response = self.client.get(reverse("listar_cliente"), {"q": "(11) 98888"})

        self.assertContains(response, "João Souza")
        self.assertNotContains(response, "Maria Silva")

    def test_list_shows_message_when_search_has_no_results(self):
        response = self.client.get(reverse("listar_cliente"), {"q": "cliente inexistente"})

        self.assertContains(response, 'Nenhum cliente encontrado para "cliente inexistente".')
        self.assertContains(response, "Limpar")

    def test_invalid_cpf_is_not_saved(self):
        response = self.client.post(
            reverse("criar_cliente"),
            {"nome": "Joao Souza", "cpf": "11144477734", "telefone": "11988887777"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Informe um CPF válido.")
        self.assertEqual(Cliente.objects.count(), 1)

    def test_edit_cliente(self):
        response = self.client.post(
            reverse("editar_cliente", args=[self.cliente.pk]),
            {
                "nome": "Maria Santos",
                "cpf": self.cliente.cpf,
                "telefone": "11988887777",
            },
        )

        self.assertRedirects(response, reverse("listar_cliente"))
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.nome, "Maria Santos")

    def test_delete_requires_post_confirmation(self):
        confirmation = self.client.get(
            reverse("excluir_cliente", args=[self.cliente.pk])
        )
        self.assertEqual(confirmation.status_code, 200)
        self.assertTrue(Cliente.objects.filter(pk=self.cliente.pk).exists())

        response = self.client.post(
            reverse("excluir_cliente", args=[self.cliente.pk])
        )

        self.assertRedirects(response, reverse("listar_cliente"))
        self.assertFalse(Cliente.objects.filter(pk=self.cliente.pk).exists())
