from django.shortcuts import render
from .models import Produto

def produto(request):
    produtos = Produto.objects.all()
    return render(request, 'listar_produto.html', {'produtos' : produtos})
