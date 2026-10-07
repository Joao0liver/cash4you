from django.urls import path
from . import views

urlpatterns = [
    path("", views.listar_agendamento, name="listar_agendamento"),
    path("novo/", views.criar_agendamento, name="criar_agendamento"),
    path("<int:id>/editar/", views.editar_agendamento, name="editar_agendamento"),
    path("<int:id>/excluir/", views.excluir_agendamento, name="excluir_agendamento"),
]
