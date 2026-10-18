from django.urls import path

from . import views

app_name = "configuracao"

urlpatterns = [
    path("estabelecimento/", views.configurar_estabelecimento, name="configurar_estabelecimento"),
]