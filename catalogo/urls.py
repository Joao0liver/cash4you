from django.urls import path
from . import views

urlpatterns = [
    # Caminhos de Produto
    path('produto/', views.listar_produto, name='listar_produto'),
    path('produto/cadastrar/', views.cadastrar_produto, name='cadastrar_produto'),
    path('produto/editar/<int:id>', views.editar_produto, name='editar_produto'),
    path('produto/excluir/<int:id>', views.excluir_produto, name='excluir_produto'),

    # Caminhos de Serviço
    path('servico/', views.listar_servico, name='listar_servico'),
    path('servico/cadastrar/', views.cadastrar_servico, name='cadastrar_servico'),
    path('servico/editar/<int:id>', views.editar_servico, name='editar_servico'),
    path('servico/excluir/<int:id>', views.excluir_servico, name='excluir_servico'),
]