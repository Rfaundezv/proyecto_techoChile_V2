from django.urls import path
from . import views

app_name = 'viviendas'

urlpatterns = [
    path('', views.lista_viviendas, name='lista'),
]
