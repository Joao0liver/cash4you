from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

def redirecionar_por_perfil(usuario):
    if usuario.groups.filter(name='Administrador').exists():
        return redirect('dashboard:home')

    if usuario.groups.filter(name='Gerente').exists():
        return redirect('dashboard:home')

    if usuario.groups.filter(name='Funcionário').exists():
        return redirect('dashboard:home')

    return redirect('dashboard:home')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    form = AuthenticationForm(
        request=request,
        data=request.POST or None,
    )

    if request.method == 'POST' and form.is_valid():
        usuario = form.get_user()
        login(request, usuario)

        return redirecionar_por_perfil(usuario)

    return render(
        request,
        'autenticacao/login.html',
        {'form': form},
    )

@login_required
def inicio(request):
    return render(request, 'dashboard/home.html')

@require_POST
@login_required
def logout_view(request):
    logout(request)
    return redirect('autenticacao:login')