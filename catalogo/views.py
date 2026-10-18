from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Produto, Servico
from .forms import ProdutoForm, ServicoForm

# Views de Produto
@login_required
def listar_produto(request):
    produtos = Produto.objects.all()
    return render(request, 'catalogo/produto/listar_produto.html', {'produtos' : produtos})

@login_required
def cadastrar_produto(request):

    if request.method == 'POST':
        form = ProdutoForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('listar_produto')
        
    else:
        form = ProdutoForm()

    return render(request, 'catalogo/produto/form_produto.html', {'form' : form, 'titulo' : 'Cadastrar Produto'})

@login_required
def editar_produto(request, id):
    produto = get_object_or_404(Produto, id=id)

    if request.method == 'POST':
        form = ProdutoForm(request.POST, instance=produto)

        if form.is_valid():
            form.save()
            return redirect('listar_produto')
    
    else:
        form = ProdutoForm(instance=produto)

    return render(request, 'catalogo/produto/form_produto.html', {'form' : form, 'titulo' : 'Editar Produto'})

@login_required
def excluir_produto(request, id):
    produto = get_object_or_404(Produto, id=id)

    if request.method == 'POST':
        produto.delete()
        return redirect('listar_produto')

    return render(request, 'catalogo/produto/confirmar_exclusao.html', {'produto' : produto})

# Views de Serviço
@login_required
def listar_servico(request):
    servicos = Servico.objects.all()
    return render(request, 'catalogo/servico/listar_servico.html', {'servicos' : servicos})

@login_required
def cadastrar_servico(request):

    if request.method == 'POST':
        form = ServicoForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('listar_servico')
        
    else:
        form = ServicoForm()

    return render(request, 'catalogo/servico/form_servico.html', {'form' : form, 'titulo' : 'Cadastrar Serviço'})

@login_required
def editar_servico(request, id):
    servico = get_object_or_404(Servico, id=id)

    if request.method == 'POST':
        form = ServicoForm(request.POST, instance=servico)

        if form.is_valid():
            form.save()
            return redirect('listar_servico')
    
    else:
        form = ServicoForm(instance=servico)

    return render(request, 'catalogo/servico/form_servico.html', {'form' : form, 'titulo' : 'Editar Serviço'})

@login_required
def excluir_servico(request, id):
    servico = get_object_or_404(Servico, id=id)

    if request.method == 'POST':
        servico.delete()
        return redirect('listar_servico')

    return render(request, 'catalogo/servico/confirmar_exclusao.html', {'servico' : servico})
