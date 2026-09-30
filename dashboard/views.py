from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from cliente.models import Cliente
from catalogo.models import Produto

# @login_required
def dashboard(request):
    total_clientes = Cliente.objects.count();
    total_produtos = Produto.objects.count();

    context = {
        'total_clientes': total_clientes,
        'total_produtos': total_produtos,
        'total_vendas': 0,
    }

    return render(request, 'dashboard/home.html', context)