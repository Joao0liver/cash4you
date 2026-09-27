from django.shortcuts import render
from .models import Cliente

def cliente(request):
    clientes = Cliente.objects.all()
    return render(request, 'listar_cliente.html', {'clientes' : clientes})
