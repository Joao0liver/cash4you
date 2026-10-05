from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_cliente, name='listar_cliente'),
    path('cadastrar/', views.cadastrar_cliente, name='cadastrar_cliente'),
    path('editar/<int:id>/', views.editar_cliente, name='editar_cliente'),
]
