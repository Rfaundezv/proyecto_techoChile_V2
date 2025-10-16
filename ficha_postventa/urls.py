from django.urls import path
from . import views

app_name = 'ficha_postventa'

urlpatterns = [
    # Dashboard y listado
    path('', views.dashboard_fichas, name='dashboard'),
    path('listar/', views.listar_fichas, name='listar'),
    
    # CRUD de fichas
    path('crear/', views.crear_ficha, name='crear'),
    path('<int:pk>/', views.ver_ficha, name='detalle'),
    path('<int:pk>/editar/', views.editar_ficha, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_ficha, name='eliminar'),
    
    # Archivos y documentos
    path('<int:ficha_pk>/subir-archivo/', views.subir_archivo, name='subir_archivo'),
    path('<int:pk>/pdf/', views.generar_pdf, name='generar_pdf'),
    
    # Estadísticas
    path('proyecto/<int:proyecto_pk>/estadisticas/', views.estadisticas_proyecto, name='estadisticas_proyecto'),
    
    # AJAX endpoints
    path('ajax/viviendas/', views.ajax_viviendas_por_proyecto, name='ajax_viviendas'),
    path('ajax/buscar-beneficiario/', views.ajax_buscar_beneficiario, name='ajax_buscar_beneficiario'),
]