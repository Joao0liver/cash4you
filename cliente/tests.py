from django.test import TestCase
from .forms import ClienteForm

class ClienteFormTestCase(TestCase):

    def test_cpf_valido_deve_ser_aceito(self):
        dados = {
            'nome': 'Cliente Teste',
            'cpf': '52998224725',
            'telefone': '11999999999',
        }

        form = ClienteForm(data=dados)

        self.assertTrue(
            form.is_valid(),
            form.errors
        )

        self.assertEqual(
            form.cleaned_data['cpf'],
            '52998224725'
        )

    def test_cpf_invalido_deve_ser_rejeitado(self):
        dados = {
            'nome': 'Cliente Teste',
            'cpf': '11111111111',
            'telefone': '11999999999',
        }

        form = ClienteForm(data=dados)

        self.assertFalse(
            form.is_valid()
        )

        self.assertIn(
            'cpf', 
            form.errors
        )