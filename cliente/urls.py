from django.urls import path
from . import views

urlpatterns = [
    path('', views.cliente, name='listar_cliente'),
]
