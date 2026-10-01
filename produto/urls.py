from django.urls import path
from . import views

urlpatterns = [
    path('', views.produto, name='listar_produto'),
    path('novo/', views.criar_produto, name='criar_produto'),
    path('<int:pk>/editar/', views.editar_produto, name='editar_produto'),
    path('<int:pk>/excluir/', views.excluir_produto, name='excluir_produto'),
]
