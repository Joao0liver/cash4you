from django.urls import path

from . import views


urlpatterns = [
    path("", views.caixa, name="caixa"),
    path("historico/", views.listar_vendas, name="listar_vendas"),
    path("<int:pk>/editar/", views.editar_venda, name="editar_venda"),
    path("<int:pk>/excluir/", views.excluir_venda, name="excluir_venda"),
    path("<int:pk>/", views.detalhe_venda, name="detalhe_venda"),
]
