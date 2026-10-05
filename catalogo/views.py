from django.shortcuts import render, redirect
from .models import Produto, Servico
from .forms import ProdutoForm

def listar_produto(request):
    produtos = Produto.objects.all()
    return render(request, 'catalogo/produto/listar_produto.html', {'produtos' : produtos})

def cadastrar_produto(request):

    if request.method == 'POST':
        form = ProdutoForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('listar_produto')
        
    else:
        form = ProdutoForm()

    return render(request, 'catalogo/produto/form_produto.html', {'form' : form, 'titulo' : 'Cadastrar Produto'})

def servico(request):
    servicos = Servico.objects.all()
    return render(request, 'catalogo/servico/listar_servico.html', {'servicos' : servicos})
