from django.urls import path
from . import views

urlpatterns = [
    path('', views.cliente, name='listar_cliente'),
    path('novo/', views.criar_cliente, name='criar_cliente'),
    path('<int:pk>/editar/', views.editar_cliente, name='editar_cliente'),
    path('<int:pk>/excluir/', views.excluir_cliente, name='excluir_cliente'),
]
