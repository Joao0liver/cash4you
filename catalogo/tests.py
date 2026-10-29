from django.test import TestCase
from .forms import ProdutoForm

class ProdutoFormTestCase(TestCase):

    def test_preco_venda_nao_pode_ser_menor_que_custo(self):
        dados = {
            'descricao': 'Produto Teste',
            'preco_venda': '10.00',
            'preco_custo': '15.00',
            'quantidade': '5',
        }

        form = ProdutoForm(data=dados)

        self.assertFalse(
            form.is_valid()
        )

        self.assertTrue(
            form.non_field_errors()
        )