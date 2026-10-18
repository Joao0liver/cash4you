from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import DadosEstabelecimento
from .forms import DadosEstabelecimentoForm

@login_required
def configurar_estabelecimento(request):
    dados_estabelecimento = DadosEstabelecimento.objects.filter(id=1).first()
    if dados_estabelecimento is None:
        dados_estabelecimento = DadosEstabelecimento(id=1)
    form = DadosEstabelecimentoForm(
        request.POST or None,
        instance=dados_estabelecimento,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(
            request,
            "Dados do estabelecimento salvos para os próximos comprovantes.",
        )
        return redirect("configurar_estabelecimento")
    return render(
        request,
        "dadosEstabelecimento/configurar_estabelecimento.html",
        {"form": form},
    )
