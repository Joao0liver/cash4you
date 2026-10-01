from django.urls import path

from . import views


urlpatterns = [
    path("", views.listar_agendamentos, name="listar_agendamentos"),
    path("novo/", views.criar_agendamento, name="criar_agendamento"),
    path("<int:pk>/editar/", views.editar_agendamento, name="editar_agendamento"),
    path("<int:pk>/excluir/", views.excluir_agendamento, name="excluir_agendamento"),
]
