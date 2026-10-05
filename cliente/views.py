from django.shortcuts import render, redirect, get_object_or_404
from .models import Cliente
from .forms import ClienteForm

def listar_cliente(request):

    clientes = Cliente.objects.all()
    return render(request, 'listar_cliente.html', {'clientes' : clientes})

def cadastrar_cliente(request):

    if request.method == 'POST':
        form = ClienteForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('listar_cliente')
        
    else:
        form = ClienteForm()

    return render(request, 'form_cliente.html', {'form' : form, 'titulo' : 'Cadastrar Cliente'})

def editar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)

    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)

        if form.is_valid():
            form.save()
            return redirect('listar_cliente')
    
    else:
        form = ClienteForm(instance=cliente)

    return render(request, 'form_cliente.html', {'form' : form, 'titulo' : 'Editar Cliente'})

def excluir_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)

    if request.method == 'POST':
        cliente.delete()
        return redirect('listar_cliente')

    return render(request, 'confirmar_exclusao.html', {'cliente' : cliente})
