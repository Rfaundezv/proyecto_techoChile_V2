 
from django.urls import path
from . import views
from . import views_filtrar_observaciones

app_name = 'reportes'

urlpatterns = [
        # Página principal de reportes
        path('', views.index, name='index'),
        path('observaciones/filtrar/', views_filtrar_observaciones.reporte_observaciones_filtradas, name='reporte_observaciones_filtradas'),
        path('observaciones/filtrar_excel/', views_filtrar_observaciones.reporte_observaciones_filtradas_excel, name='reporte_observaciones_filtradas_excel'),
        # Reportes Excel
        path('actas/entregas_excel/', views.reporte_entregas_excel, name='reporte_entregas_excel'),
        path('observaciones/abiertas_excel/', views.reporte_observaciones_abiertas_excel, name='reporte_observaciones_abiertas_excel'),
        path('observaciones/cerradas_excel/', views.reporte_observaciones_cerradas_excel, name='reporte_observaciones_cerradas_excel'),
        path('observaciones/abiertas_urgentes_excel/', views.reporte_observaciones_abiertas_urgentes_excel, name='reporte_observaciones_abiertas_urgentes_excel'),
        path('observaciones/cerradas_urgentes_excel/', views.reporte_observaciones_cerradas_urgentes_excel, name='reporte_observaciones_cerradas_urgentes_excel'),
        path('beneficiarios_por_proyecto_excel/', views.reporte_beneficiarios_por_proyecto_excel, name='reporte_beneficiarios_por_proyecto_excel'),
        path('viviendas_sin_beneficiario_excel/', views.reporte_viviendas_sin_beneficiario_excel, name='reporte_viviendas_sin_beneficiario_excel'),
        path('viviendas_sin_observaciones_excel/', views.reporte_viviendas_sin_observaciones_excel, name='reporte_viviendas_sin_observaciones_excel'),
        path('reporte_total_excel/', views.reporte_total_excel, name='reporte_total_excel'),
        path('observaciones/en_ejecucion_excel/', views.reporte_observaciones_en_ejecucion_excel, name='reporte_observaciones_en_ejecucion_excel'),
        path('observaciones/urgentes_pendientes_excel/', views.reporte_observaciones_urgentes_pendientes_excel, name='reporte_observaciones_urgentes_pendientes_excel'),
        path('observaciones/urgentes_cerradas_excel/', views.reporte_observaciones_urgentes_cerradas_excel, name='reporte_observaciones_urgentes_cerradas_excel'),
        path('observaciones/urgentes_abiertas_excel/', views.reporte_observaciones_urgentes_abiertas_excel, name='reporte_observaciones_urgentes_abiertas_excel'),
        path('estadisticas/region_excel/', views.reporte_estadisticas_region_excel, name='reporte_estadisticas_region_excel'),
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

        # Reportes PDF generados
        path('reportes-generados/', views.listar_reportes_generados, name='listar_reportes_generados'),
        path('reportes-generados/<int:reporte_id>/descargar/', views.descargar_reporte_generado, name='descargar_reporte_generado'),
        ]