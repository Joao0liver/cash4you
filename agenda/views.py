from datetime import date, datetime, timedelta
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
# from conta_pagar.models import Funcionario
from .forms import AgendamentoForm, horarios_disponiveis
from .models import Agendamento, HorarioAgendado

def _obter_horarios(
    data_selecionada,
    agenda_key=None,
    agendamento=None,
    selecionados=None,
):
    horarios_ocupados = HorarioAgendado.objects.filter(
        data=data_selecionada,
        agenda_key=agenda_key,
    )
    if not agenda_key:
        horarios_ocupados = HorarioAgendado.objects.none()
    if agendamento is not None:
        horarios_ocupados = horarios_ocupados.exclude(agendamento=agendamento)
    ocupados = {
        horario.inicio.strftime("%H:%M")
        for horario in horarios_ocupados
    }
    if selecionados is None and agendamento is not None:
        selecionados = {
            horario.inicio.strftime("%H:%M")
            for horario in agendamento.horarios.filter(data=data_selecionada)
        }
    selecionados = set(selecionados or [])

    resultado = []
    for valor, rotulo in horarios_disponiveis():
        resultado.append(
            {
                "valor": valor,
                "rotulo": rotulo,
                "disponivel": valor not in ocupados,
                "selecionado": valor in selecionados,
            }
        )
    return resultado


def _chave_agenda_selecionada(request, agendamento=None):
    dados = request.POST if request.method == "POST" else request.GET
    if "tipo_agendar_para" in dados:
        tipo = dados.get("tipo_agendar_para")
        if tipo == "funcionario":
            funcionario_id = dados.get("funcionario")
            if funcionario_id and funcionario_id.isdigit():
                funcionario = Funcionario.objects.filter(pk=funcionario_id).first()
                if funcionario:
                    return f"funcionario:{funcionario.pk}"
        elif tipo == "manual":
            descricao = dados.get("descricao_agendar_para", "").strip()
            if descricao:
                return f"descricao:{descricao}"
        return None

    if agendamento is not None:
        return agendamento.agenda_key
    return None


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


def listar_agendamentos(request):
    agendamentos = Agendamento.objects.select_related("funcionario").prefetch_related(
        "servicos", "horarios"
    )
    return render(
        request,
        "agenda/listar_agendamentos.html",
        {"agendamentos": agendamentos},
    )


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
            "descricao_agendar_para": request.GET.get(
                "descricao_agendar_para", ""
            ),
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

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                agendamento = form.save()
                inicio_horarios = [
                    datetime.strptime(valor, "%H:%M").time()
                    for valor in form.cleaned_data["horarios"]
                ]
                HorarioAgendado.objects.bulk_create(
                    [
                        HorarioAgendado(
                            agendamento=agendamento,
                            data=form.cleaned_data["data"],
                            agenda_key=agendamento.agenda_key,
                            inicio=inicio,
                            fim=(
                                datetime.combine(form.cleaned_data["data"], inicio)
                                + timedelta(minutes=30)
                            ).time(),
                        )
                        for inicio in inicio_horarios
                    ]
                )
        except IntegrityError:
            form.add_error(
                "horarios",
                "Um ou mais horários acabaram de ser reservados. Atualize a página e tente novamente.",
            )
        else:
            return redirect("listar_agendamentos")

    return render(
        request,
        "agenda/form_agendamento.html",
        {
            "form": form,
            "horarios": _obter_horarios(
                data_selecionada,
                agenda_key=_chave_agenda_selecionada(request),
                selecionados=selecionados,
            ),
            "data_selecionada": data_selecionada,
            "agenda_key": _chave_agenda_selecionada(request),
            "tipo_filtro": tipo_filtro,
            "funcionario_filtro": funcionario_filtro,
            "descricao_filtro": descricao_filtro,
            "titulo": "Novo agendamento",
            "botao": "Confirmar agendamento",
        },
    )


def editar_agendamento(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk)
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
                "descricao_agendar_para": request.GET.get(
                    "descricao_agendar_para", ""
                ),
            }
            if request.method == "GET" and "tipo_agendar_para" in request.GET
            else None
        ),
        selected_date=data_selecionada,
    )
    tipo_filtro, funcionario_filtro, descricao_filtro = _valores_filtro_agenda(
        request, form
    )
    selecionados = request.POST.getlist("horarios") if request.method == "POST" else None

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                agendamento = form.save()
                agendamento.horarios.all().delete()
                inicio_horarios = [
                    datetime.strptime(valor, "%H:%M").time()
                    for valor in form.cleaned_data["horarios"]
                ]
                HorarioAgendado.objects.bulk_create(
                    [
                        HorarioAgendado(
                            agendamento=agendamento,
                            data=form.cleaned_data["data"],
                            agenda_key=agendamento.agenda_key,
                            inicio=inicio,
                            fim=(
                                datetime.combine(form.cleaned_data["data"], inicio)
                                + timedelta(minutes=30)
                            ).time(),
                        )
                        for inicio in inicio_horarios
                    ]
                )
        except IntegrityError:
            form.add_error(
                "horarios",
                "Um ou mais horários acabaram de ser reservados. Atualize a página e tente novamente.",
            )
        else:
            return redirect("listar_agendamentos")

    return render(
        request,
        "agenda/form_agendamento.html",
        {
            "form": form,
            "horarios": _obter_horarios(
                data_selecionada,
                agenda_key=_chave_agenda_selecionada(request, agendamento),
                agendamento=agendamento,
                selecionados=selecionados,
            ),
            "data_selecionada": data_selecionada,
            "agenda_key": _chave_agenda_selecionada(request, agendamento),
            "tipo_filtro": tipo_filtro,
            "funcionario_filtro": funcionario_filtro,
            "descricao_filtro": descricao_filtro,
            "titulo": "Editar agendamento",
            "botao": "Salvar alterações",
            "agendamento": agendamento,
        },
    )


def excluir_agendamento(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk)
    if request.method == "POST":
        agendamento.delete()
        return redirect("listar_agendamentos")

    return render(
        request,
        "agenda/confirmar_exclusao.html",
        {"agendamento": agendamento},
    )
