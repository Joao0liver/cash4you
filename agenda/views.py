from datetime import date, datetime, timedelta
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from .forms import AgendamentoForm, horarios_disponiveis
from .models import Agendamento, HorarioAgendado
from usuario.models import Usuario

def obter_horarios(data_selecionada, funcionario_id=None, descricao_agendar_para=None, agendamento=None, selecionados=None):
    horarios_ocupados = HorarioAgendado.objects.filter(
        agendamento__data = data_selecionada
    )

    if funcionario_id:
        horarios_ocupados = horarios_ocupados.filter(
            agendamento__funcionario_id = funcionario_id
        )
    elif descricao_agendar_para:
        horarios_ocupados = horarios_ocupados.filter(
            agendamento__funcionario__isnull = True,
            agendamento__descricao_agendar_para = descricao_agendar_para.strip(),
        )
    else:
        horarios_ocupados = HorarioAgendado.objects.none()

    if agendamento is not None:
        horarios_ocupados = horarios_ocupados.exclude(
            agendamento = agendamento
        )

    ocupados = {
        horario.inicio.strftime('%H:%M')
        for horario in horarios_ocupados
    }

    if selecionados is None and agendamento is not None:
        if agendamento.data == data_selecionada:
            selecionados = {
                horario.inicio.strftime('%H:%M')
                for horario in agendamento.horarios.all()
            }

    selecionados = set(selecionados or [])

    resultado = []

    for valor, rotulo in horarios_disponiveis():
        resultado.append(
            {
                'valor': valor,
                'rotulo': rotulo,
                'disponivel': valor not in ocupados,
                'selecionado': valor in selecionados,
            }
        )

    return resultado

def recurso_selecionado(request, agendamento=None):
    dados = request.POST if request.method == 'POST' else request.GET

    if 'tipo_agendar_para' in dados:

        tipo = dados.get('tipo_agendar_para')

        if tipo == 'funcionario':

            funcionario_id = dados.get('funcionario')

            if funcionario_id and funcionario_id.isdigit():

                funcionario = Usuario.objects.filter(
                    id = funcionario_id,
                    groups__name = 'Funcionário',
                ).first()

                if funcionario:
                    return funcionario.id, None
        
        elif tipo == 'manual':

            descricao = dados.get('descricao_agendar_para', '').strip()

            if descricao:
                return None, descricao

        return None, None

    # O filtro não é enviado na edição
    if agendamento is not None:

        if agendamento.funcionario_id:
            return agendamento.funcionario_id, None

        if agendamento.descricao_agendar_para:
            return None, agendamento.descricao_agendar_para.strip()

    return None, None
            
def _valores_filtro_agenda(request, form):
    if request.method == "POST":
        dados = request.POST
        return (
            dados.get("tipo_agendar_para", ""),
            dados.get("funcionario", ""),
            dados.get("descricao_agendar_para", ""),
        )

    return (
        form["tipo_agendar_para"].value() or "",
        form["funcionario"].value() or "",
        form["descricao_agendar_para"].value() or "",
    )

def _data_selecionada(valor, fallback):
    data = parse_date(valor or "")
    return data or fallback

def listar_agendamento(request):
    agendamentos = Agendamento.objects.select_related("funcionario").prefetch_related(
        "servicos", "horarios"
    )
    
    return render(request, "agenda/listar_agendamento.html", {"agendamentos": agendamentos})

def criar_agendamento(request):
    data_selecionada = _data_selecionada(
        request.POST.get("data") if request.method == "POST" else request.GET.get("data"),
        date.today(),
    )

    initial = {}

    if request.method == "GET" and "tipo_agendar_para" in request.GET:
        initial = {
            "tipo_agendar_para": request.GET.get("tipo_agendar_para", ""),
            "funcionario": request.GET.get("funcionario", ""),
            "descricao_agendar_para": request.GET.get("descricao_agendar_para", ""),
        }

    form = AgendamentoForm(
        request.POST or None,
        initial=initial,
        selected_date=data_selecionada,
    )
    tipo_filtro, funcionario_filtro, descricao_filtro = _valores_filtro_agenda(
        request, form
    )

    selecionados = request.POST.getlist("horarios") if request.method == "POST" else None

    funcionario_id, descricao_agendar_para = recurso_selecionado(request)

    if request.method == "POST" and form.is_valid():

        agendamento = form.save()

        inicio_horarios = [
            datetime.strptime(valor, '%H:%M').time()
            for valor in form.cleaned_data['horarios']
        ]

        for inicio in inicio_horarios:

            fim = (
                datetime.combine(agendamento.data, inicio) + timedelta(minutes=30)
            ).time()

            HorarioAgendado.objects.create(agendamento=agendamento, inicio=inicio, fim=fim)

        return redirect('listar_agendamento')

    return render(
        request,
        "agenda/form_agendamento.html",
        {
            "form": form,
            "horarios": obter_horarios(
                data_selecionada,
                funcionario_id=funcionario_id,
                descricao_agendar_para=descricao_agendar_para,
                selecionados=selecionados,
            ),
            "data_selecionada": data_selecionada,
            "tipo_filtro": tipo_filtro,
            "funcionario_filtro": funcionario_filtro,
            "descricao_filtro": descricao_filtro,
            "titulo": "Novo agendamento",
            "botao": "Confirmar agendamento",
        },
    )

def editar_agendamento(request, id):
    agendamento = get_object_or_404(Agendamento, id=id)

    data_selecionada = _data_selecionada(
        request.POST.get("data") if request.method == "POST" else request.GET.get("data"),
        agendamento.data,
    )

    form = AgendamentoForm(
        request.POST or None,
        instance=agendamento,
        initial=(
            {
                "tipo_agendar_para": request.GET.get("tipo_agendar_para", ""),
                "funcionario": request.GET.get("funcionario", ""),
                "descricao_agendar_para": request.GET.get("descricao_agendar_para", ""),
            }
            if request.method == "GET" and "tipo_agendar_para" in request.GET else None
        ),
        selected_date=data_selecionada,
    )
    tipo_filtro, funcionario_filtro, descricao_filtro = _valores_filtro_agenda(
        request, form
    )

    selecionados = request.POST.getlist("horarios") if request.method == "POST" else None

    funcionario_id, descricao_agendar_para = recurso_selecionado(request, agendamento,)

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():

                agendamento = form.save()

                # Remove os horários antigos
                agendamento.horarios.all().delete()

                inicio_horarios = [
                    datetime.strptime(valor, '%H:%M').time()
                    for valor in form.cleaned_data['horarios']
                ]

                HorarioAgendado.objects.bulk_create(
                    [
                        HorarioAgendado(
                            agendamento = agendamento,
                            inicio = inicio,
                            fim = (datetime.combine(agendamento.data, inicio) + timedelta(minutes=30)).time()
                        )
                        for inicio in inicio_horarios
                    ]
                )
        except IntegrityError:
            form.add_error(
                'horarios', 
                'Um ou mais horários acabaram de ser reservados. ',
                'Atualize a página e tente novamente.'
            )
        else:
            return redirect('listar_agendamento')

    return render(
        request,
        "agenda/form_agendamento.html",
        {
            "form": form,
            "horarios": obter_horarios(
                data_selecionada,
                funcionario_id=funcionario_id,
                descricao_agendar_para=descricao_agendar_para,
                agendamento=agendamento,
                selecionados=selecionados,
            ),
            "data_selecionada": data_selecionada,
            "tipo_filtro": tipo_filtro,
            "funcionario_filtro": funcionario_filtro,
            "descricao_filtro": descricao_filtro,
            "titulo": "Editar agendamento",
            "botao": "Salvar alterações",
            "agendamento": agendamento,
        },
    )

def excluir_agendamento(request, id):
    agendamento = get_object_or_404(Agendamento, id=id)

    if request.method == "POST":
        agendamento.delete()
        return redirect("listar_agendamento")

    return render(
        request,
        "agenda/confirmar_exclusao.html",
        {"agendamento": agendamento},
    )
