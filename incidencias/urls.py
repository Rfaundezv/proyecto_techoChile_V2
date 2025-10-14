
from django.urls import path
from . import views
from . import views_movil

app_name = 'incidencias'

urlpatterns = [
    path('', views.lista_observaciones, name='lista_observaciones'),
    path('crear/', views.crear_observacion, name='crear_observacion'),
    path('<int:pk>/', views.detalle_observacion, name='detalle_observacion'),
    path('<int:pk>/cambiar-estado/', views.cambiar_estado_observacion, name='cambiar_estado'),
    path('archivo/<int:pk>/eliminar/', views.eliminar_archivo_observacion, name='eliminar_archivo'),
    path('ajax/viviendas/', views.ajax_viviendas_por_proyecto, name='ajax_viviendas'),
    path('ajax/recintos/', views.ajax_recintos_por_proyecto, name='ajax_recintos'),
    path('ajax/recintos-vivienda/', views.ajax_recintos_por_vivienda, name='ajax_recintos_vivienda'),
    path('ajax/elementos/', views.ajax_elementos_por_recinto, name='ajax_elementos'),
    path('archivos/<int:pk>/', views.ObservacionArchivosView.as_view(), name='incidencias_observacion_archivos'),
    
    # URLs móviles
    path('movil/', views_movil.observaciones_movil, name='observaciones_movil'),
    path('movil/api/', views_movil.observaciones_api_movil, name='observaciones_api_movil'),
    path('movil/cambiar-estado/<int:observacion_id>/', views_movil.cambiar_estado_movil, name='cambiar_estado_movil'),
    path('movil/actualizar-descripcion/<int:observacion_id>/', views_movil.actualizar_descripcion_movil, name='actualizar_descripcion_movil'),
    path('movil/descripcion-completa/<int:observacion_id>/', views_movil.obtener_descripcion_completa, name='obtener_descripcion_completa'),
    path('movil/subir-archivo/<int:observacion_id>/', views_movil.subir_archivo_movil, name='subir_archivo_movil'),
    path('movil/agregar-comentario/<int:observacion_id>/', views_movil.agregar_comentario_movil, name='agregar_comentario_movil'),
    path('movil/comentarios/<int:observacion_id>/', views_movil.obtener_comentarios_movil, name='obtener_comentarios_movil'),
    path('movil/detalle/<int:observacion_id>/', views_movil.observacion_detalle_movil, name='observacion_detalle_movil'),
    path('movil/crear_observacion/', views_movil.crear_observacion_movil, name='crear_observacion_movil'),
]
