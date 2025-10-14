from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    # Página principal de reportes
    path('', views.index, name='index'),
    
    # Actas de recepción
    path('actas/', views.acta_list, name='acta_list'),
    path('actas/crear/', views.acta_create, name='acta_create'),
    path('actas/<int:pk>/', views.acta_detail, name='acta_detail'),
    path('actas/<int:pk>/editar/', views.acta_edit, name='acta_edit'),
    path('actas/<int:pk>/eliminar/', views.acta_delete, name='acta_delete'),
    path('actas/<int:pk>/pdf/', views.acta_pdf, name='acta_pdf'),
    
    # AJAX endpoints
    path('ajax/buscar-beneficiario/', views.buscar_beneficiario_ajax, name='buscar_beneficiario_ajax'),
    path('api/viviendas-por-proyecto/', views.get_viviendas_by_proyecto, name='viviendas_por_proyecto'),
    path('api/datos-vivienda/', views.get_vivienda_data, name='datos_vivienda'),
]