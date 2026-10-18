from django.urls import path

from . import views

urlpatterns = [
    path("configuracoes/", views.configurar_estabelecimento, name="configurar_estabelecimento"),
]