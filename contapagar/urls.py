from django.urls import path
from . import views

app_name = 'contapagar'

urlpatterns = [
    path("", views.listar_contas, name="listar_contas_pagar"),
    path("nova/", views.criar_conta, name="criar_conta_pagar"),
    path("<int:id>/editar/", views.editar_conta, name="editar_conta_pagar"),
    path("<int:id>/status/", views.alternar_status_conta, name="alternar_status_conta"),
    path("<int:id>/excluir/", views.excluir_conta, name="excluir_conta_pagar"),
]