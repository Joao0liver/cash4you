from django.urls import path
from . import views

urlpatterns = [
    path('', views.servico, name='listar_servico'),
]
