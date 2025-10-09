
from django.contrib import admin
from .models import TipoObservacion, EstadoObservacion, Observacion, SeguimientoObservacion, ArchivoAdjuntoObservacion

@admin.register(TipoObservacion)
class TipoObservacionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre']

@admin.register(EstadoObservacion)
class EstadoObservacionAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre']
    ordering = ['codigo']

@admin.register(Observacion)
class ObservacionAdmin(admin.ModelAdmin):
    list_display = ['proyecto', 'vivienda', 'elemento', 'tipo', 'estado', 'prioridad', 'fecha_creacion', 'creado_por']
    list_filter = ['estado', 'tipo', 'prioridad', 'es_urgente', 'fecha_creacion']
    search_fields = ['elemento', 'detalle', 'proyecto__codigo', 'vivienda__codigo']
    date_hierarchy = 'fecha_creacion'

    fieldsets = (
        ('Ubicación', {
            'fields': ('proyecto', 'vivienda', 'recinto')
        }),
        ('Observación', {
            'fields': ('elemento', 'detalle', 'tipo', 'prioridad', 'es_urgente')
        }),
        ('Estado y Fechas', {
            'fields': ('estado', 'fecha_vencimiento', 'fecha_cierre')
        }),
        ('Asignación', {
            'fields': ('creado_por', 'asignado_a')
        }),
        ('Seguimiento', {
            'fields': ('observaciones_seguimiento',)
        })
    )

@admin.register(SeguimientoObservacion)
class SeguimientoObservacionAdmin(admin.ModelAdmin):
    list_display = ['observacion', 'fecha', 'usuario', 'accion']
    list_filter = ['fecha', 'accion', 'usuario']
    search_fields = ['observacion__elemento', 'accion', 'comentario']
    date_hierarchy = 'fecha'

@admin.register(ArchivoAdjuntoObservacion)
class ArchivoAdjuntoObservacionAdmin(admin.ModelAdmin):
    list_display = ['observacion', 'nombre_original', 'descripcion', 'fecha_subida', 'subido_por']
    list_filter = ['fecha_subida', 'subido_por']
    search_fields = ['nombre_original', 'descripcion', 'observacion__elemento']
    date_hierarchy = 'fecha_subida'
    readonly_fields = ['fecha_subida']
