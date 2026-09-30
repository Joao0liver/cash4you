from django.urls import path
from . import views

urlpatterns = [
    path('produto/', views.produto, name='listar_produto'),
    path('servico/', views.servico, name='listar_servico'),
]