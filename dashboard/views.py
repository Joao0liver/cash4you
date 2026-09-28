from django.contrib.auth.decorators import login_required
from django.shortcuts import render


# @login_required
def dashboard(request):
    context = {
        'total_usuarios': 0,
        'total_clientes': 0,
        'total_operacoes': 0,
    }

    return render(request, 'dashboard/home.html', context)