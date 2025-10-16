
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.dashboard, name='dashboard'),
    path('maestro/', core_views.maestro, name='maestro_index'),
    # CRUD Maestro
    path('maestro/regiones/', core_views.RegionList.as_view(), name='maestro_region_list'),
    path('maestro/regiones/crear/', core_views.RegionCreate.as_view(), name='maestro_region_create'),
    path('maestro/regiones/<int:pk>/editar/', core_views.RegionUpdate.as_view(), name='maestro_region_edit'),
    path('maestro/regiones/<int:pk>/eliminar/', core_views.RegionDelete.as_view(), name='maestro_region_delete'),
    path('maestro/comunas/', core_views.ComunaList.as_view(), name='maestro_comuna_list'),
    path('maestro/comunas/crear/', core_views.ComunaCreate.as_view(), name='maestro_comuna_create'),
    path('maestro/comunas/<int:pk>/editar/', core_views.ComunaUpdate.as_view(), name='maestro_comuna_edit'),
    path('maestro/comunas/<int:pk>/eliminar/', core_views.ComunaDelete.as_view(), name='maestro_comuna_delete'),
    path('maestro/roles/', core_views.RolList.as_view(), name='maestro_rol_list'),
    path('maestro/roles/crear/', core_views.RolCreate.as_view(), name='maestro_rol_create'),
    path('maestro/roles/<int:pk>/editar/', core_views.RolUpdate.as_view(), name='maestro_rol_edit'),
    path('maestro/roles/<int:pk>/eliminar/', core_views.RolDelete.as_view(), name='maestro_rol_delete'),
    path('maestro/roles/<int:pk>/activar/', core_views.RolActivate.as_view(), name='maestro_rol_activate'),
    path('maestro/constructoras/', core_views.ConstructoraList.as_view(), name='maestro_constructora_list'),
    path('maestro/constructoras/crear/', core_views.ConstructoraCreate.as_view(), name='maestro_constructora_create'),
    path('maestro/constructoras/<int:pk>/editar/', core_views.ConstructoraUpdate.as_view(), name='maestro_constructora_edit'),
    path('maestro/constructoras/<int:pk>/eliminar/', core_views.ConstructoraDelete.as_view(), name='maestro_constructora_delete'),
    path('maestro/beneficiarios/', core_views.BeneficiarioList.as_view(), name='maestro_beneficiario_list'),
    path('maestro/beneficiarios/crear/', core_views.BeneficiarioCreate.as_view(), name='maestro_beneficiario_create'),
    path('maestro/beneficiarios/<int:pk>/editar/', core_views.BeneficiarioUpdate.as_view(), name='maestro_beneficiario_edit'),
    path('maestro/beneficiarios/<int:pk>/eliminar/', core_views.BeneficiarioDelete.as_view(), name='maestro_beneficiario_delete'),
    path('maestro/usuarios/', core_views.UsuarioList.as_view(), name='maestro_usuario_list'),
    path('maestro/usuarios/crear/', core_views.UsuarioCreate.as_view(), name='maestro_usuario_create'),
    path('maestro/usuarios/<int:pk>/editar/', core_views.UsuarioUpdate.as_view(), name='maestro_usuario_edit'),
    path('maestro/usuarios/<int:pk>/eliminar/', core_views.UsuarioDelete.as_view(), name='maestro_usuario_delete'),
    path('maestro/proyectos/', core_views.ProyectoList.as_view(), name='maestro_proyecto_list'),
    path('maestro/proyectos/crear/', core_views.ProyectoCreate.as_view(), name='maestro_proyecto_create'),
    path('maestro/proyectos/<int:pk>/editar/', core_views.ProyectoUpdate.as_view(), name='maestro_proyecto_edit'),
    path('maestro/proyectos/<int:pk>/eliminar/', core_views.ProyectoDelete.as_view(), name='maestro_proyecto_delete'),
    path('maestro/viviendas/', core_views.ViviendaList.as_view(), name='maestro_vivienda_list'),
    path('maestro/viviendas/crear/', core_views.ViviendaCreate.as_view(), name='maestro_vivienda_create'),
    path('maestro/viviendas/<int:pk>/editar/', core_views.ViviendaUpdate.as_view(), name='maestro_vivienda_edit'),
    path('maestro/viviendas/<int:pk>/eliminar/', core_views.ViviendaDelete.as_view(), name='maestro_vivienda_delete'),
    path('maestro/observaciones/', core_views.ObservacionList.as_view(), name='maestro_observacion_list'),
    path('maestro/observaciones/crear/', core_views.ObservacionCreate.as_view(), name='maestro_observacion_create'),
    path('maestro/observaciones/<int:pk>/archivos/', core_views.ObservacionArchivosView.as_view(), name='maestro_observacion_archivos'),
    path('maestro/observaciones/<int:pk>/editar/', core_views.ObservacionUpdate.as_view(), name='maestro_observacion_edit'),
    path('maestro/observaciones/<int:pk>/eliminar/', core_views.ObservacionDelete.as_view(), name='maestro_observacion_delete'),
    path('maestro/configuracion-observaciones/', core_views.ConfiguracionObservacionView.as_view(), name='maestro_configuracion_observacion'),
    path('maestro/buscar-beneficiario/', core_views.buscar_beneficiario_por_rut, name='maestro_buscar_beneficiario_rut'),
    path('proyectos/', include('proyectos.urls', namespace='proyectos')),
    path('incidencias/', include('incidencias.urls', namespace='incidencias')),
    path('reportes/', include('reportes.urls', namespace='reportes')),
    path('fichas-postventa/', include('ficha_postventa.urls', namespace='ficha_postventa')),
    path('auth/', include('django.contrib.auth.urls')),
    path('ajax/comunas/', core_views.ajax_comunas_por_region, name='ajax_comunas'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
