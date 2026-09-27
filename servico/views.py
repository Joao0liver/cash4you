from django.shortcuts import render
from .models import Servico

def servico(request):
    servicos = Servico.objects.all()
    return render(request, 'listar_servico.html', {'servicos' : servicos})
