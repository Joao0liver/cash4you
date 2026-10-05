from django.shortcuts import render, redirect
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

    return render(request, 'cadastrar_cliente.html', {'form' : form})
