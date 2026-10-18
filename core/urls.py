from django.contrib import admin
from django.urls import path, include
from django.views.debug import default_urlconf

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("autenticacao.urls")),

    path('dashboard/', include("dashboard.urls")),
    path('cliente/', include("cliente.urls")),
    path('catalogo/', include("catalogo.urls")),
    path('agenda/', include("agenda.urls")),
    path('venda/', include("venda.urls")),
]
