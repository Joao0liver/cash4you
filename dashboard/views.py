from django.contrib.auth.decorators import login_required
from django.shortcuts import render


# @login_required
def dashboard(request):
    context = {
        'total_clientes': 0,
        'total_produtos': 0,
        'total_vendas': 0,
    }

    return render(request, 'dashboard/home.html', context)