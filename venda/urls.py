from django.urls import path

from . import views

urlpatterns = [
    path("", views.caixa, name="caixa"),
    path("configuracoes/", views.configurar_estabelecimento, name="configurar_estabelecimento"),
    path("historico/", views.listar_vendas, name="listar_vendas"),
    path("<int:id>/editar/", views.editar_venda, name="editar_venda"),
    path("<int:id>/excluir/", views.excluir_venda, name="excluir_venda"),
    path("<int:id>/", views.detalhe_venda, name="detalhe_venda"),
]
