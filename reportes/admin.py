from django.contrib import admin
from .models import ActaRecepcion, FamiliarBeneficiario  # , ConstructorActa


@admin.register(ActaRecepcion)
class ActaRecepcionAdmin(admin.ModelAdmin):
    list_display = [
        'numero_acta', 'vivienda', 'beneficiario', 'fecha_entrega', 
        'representante_techo', 'estado_estructura', 'estado_instalaciones'
    ]
    list_filter = [
        'fecha_entrega', 'estado_estructura', 'estado_instalaciones', 
        'tipo_estructura'
    ]
    search_fields = [
        'numero_acta', 'beneficiario__nombre', 'beneficiario__apellido_paterno',
        'vivienda__codigo', 'representante_techo'
    ]
    readonly_fields = ['numero_acta', 'fecha_creacion', 'fecha_actualizacion']
    date_hierarchy = 'fecha_entrega'
    
    fieldsets = (
        ('Información General', {
            'fields': ('numero_acta', 'vivienda', 'fecha_entrega', 'lugar_entrega')
        }),
        ('Representante TECHO', {
            'fields': ('representante_techo', 'cargo_representante', 'rut_representante', 'telefono_representante')
        }),
        ('Construcción', {
            'fields': ('jefe_construccion', 'numero_voluntarios')
        }),
        ('Descripción Vivienda', {
            'fields': ('superficie_construida', 'numero_ambientes', 'tipo_estructura')
        }),
        ('Servicios Básicos', {
            'fields': ('tiene_electricidad', 'tiene_agua_potable', 'tiene_alcantarillado')
        }),
        ('Estado de Recepción', {
            'fields': ('estado_estructura', 'estado_instalaciones', 'observaciones', 'plazo_correcciones')
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FamiliarBeneficiario)
class FamiliarBeneficiarioAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'parentesco', 'rut', 'edad', 'acta_recepcion']
    list_filter = ['parentesco']
    search_fields = ['nombre_completo', 'rut', 'acta_recepcion__numero_acta']


# TEMPORALMENTE COMENTADO
# @admin.register(ConstructorActa)
# class ConstructorActaAdmin(admin.ModelAdmin):
#     list_display = ['nombre_empresa', 'representante', 'rut', 'acta']
#     search_fields = ['nombre_empresa', 'representante', 'rut', 'acta__numero_acta']