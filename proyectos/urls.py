from django.urls import path
from . import views

app_name = 'proyectos'

urlpatterns = [
    path('', views.lista_proyectos, name='lista'),
    path('crear/', views.crear_proyecto, name='crear'),
    path('<int:pk>/', views.detalle_proyecto, name='detalle'),
    path('<int:pk>/editar/', views.editar_proyecto, name='editar'),
    path('<int:proyecto_pk>/vivienda/crear/', views.crear_vivienda, name='crear_vivienda'),
    path('beneficiario/crear/', views.crear_beneficiario, name='crear_beneficiario'),
    path('buscar-beneficiario/', views.buscar_beneficiario_por_rut, name='buscar_beneficiario_rut'),
    path('<int:proyecto_pk>/viviendas/', views.lista_viviendas, name='lista_viviendas'),
]
