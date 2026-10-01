from django.urls import path
from . import views

urlpatterns = [
    path('', views.servico, name='listar_servico'),
    path('novo/', views.criar_servico, name='criar_servico'),
    path('<int:pk>/editar/', views.editar_servico, name='editar_servico'),
    path('<int:pk>/excluir/', views.excluir_servico, name='excluir_servico'),
]
