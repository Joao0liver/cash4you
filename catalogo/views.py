from django.shortcuts import render

from .models import Produto, Servico

def produto(request):
    produtos = Produto.objects.all()
    return render(request, 'catalogo/produto/listar_produto.html', {'produtos' : produtos})

def servico(request):
    servicos = Servico.objects.all()
    return render(request, 'catalogo/servico/listar_servico.html', {'servicos' : servicos})
