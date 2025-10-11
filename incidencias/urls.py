
from django.urls import path
from . import views

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
]
