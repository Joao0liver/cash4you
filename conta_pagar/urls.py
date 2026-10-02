from django.urls import path

from . import views


urlpatterns = [
    path("", views.listar_contas, name="listar_contas_pagar"),
    path("nova/", views.criar_conta, name="criar_conta_pagar"),
    path("<int:pk>/editar/", views.editar_conta, name="editar_conta_pagar"),
    path("<int:pk>/status/", views.alternar_status_conta, name="alternar_status_conta"),
    path("<int:pk>/excluir/", views.excluir_conta, name="excluir_conta_pagar"),
]
