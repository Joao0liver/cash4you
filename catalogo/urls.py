from django.urls import path
from . import views

urlpatterns = [
    path('produto/', views.listar_produto, name='listar_produto'),
    path('produto/cadastrar/', views.cadastrar_produto, name='cadastrar_produto'),
    path('produto/editar/<int:id>', views.editar_produto, name='editar_produto'),
    path('servico/', views.servico, name='listar_servico'),
]