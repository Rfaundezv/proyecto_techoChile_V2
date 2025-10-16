from django.contrib import admin
from .models import FichaPostventa, HistorialFicha, ArchivoFicha


class ArchivoFichaInline(admin.TabularInline):
    model = ArchivoFicha
    extra = 1
    readonly_fields = ('fecha_subida', 'subido_por')

    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.subido_por = request.user
        super().save_model(request, obj, form, change)


class HistorialFichaInline(admin.TabularInline):
    model = HistorialFicha
    extra = 0
    readonly_fields = ('fecha_cambio', 'usuario', 'campo_modificado', 'valor_anterior', 'valor_nuevo')


@admin.register(FichaPostventa)
class FichaPostventaAdmin(admin.ModelAdmin):
    list_display = (
        'vivienda',
        'fecha_evaluacion', 
        'evaluador',
        'puntaje_habitabilidad',
        'puntaje_satisfaccion',
        'requiere_seguimiento',
        'activa'
    )
    
    list_filter = (
        'fecha_evaluacion',
        'evaluador',
        'requiere_seguimiento',
        'activa',
        'vivienda__proyecto',
        'estado_general_vivienda',
        'satisfaccion_general'
    )
    
    search_fields = (
        'vivienda__codigo',
        'vivienda__proyecto__codigo',
        'vivienda__proyecto__nombre',
        'vivienda__familia_beneficiaria',
        'evaluador__nombre',
        'evaluador__email'
    )
    
    readonly_fields = (
        'fecha_creacion',
        'fecha_actualizacion',
        'puntaje_habitabilidad',
        'puntaje_satisfaccion',
        'puntaje_social',
        'servicios_funcionando'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'vivienda',
                'fecha_evaluacion',
                'evaluador',
                'activa'
            )
        }),
        ('Datos de la Familia', {
            'fields': (
                'familia_presente',
                'jefe_hogar_presente',
                'observaciones_familia'
            ),
            'classes': ('collapse',)
        }),
        ('Servicios Básicos', {
            'fields': (
                'agua_potable_funciona',
                'electricidad_funciona',
                'alcantarillado_funciona',
                'gas_funciona'
            ),
            'classes': ('wide',)
        }),
        ('Evaluación Técnica', {
            'fields': (
                'estado_general_vivienda',
                'estado_techumbre',
                'estado_muros',
                'estado_pisos',
                'estado_puertas_ventanas',
                'estado_instalacion_electrica',
                'estado_instalacion_sanitaria'
            ),
            'classes': ('wide',)
        }),
        ('Evaluación de Satisfacción', {
            'fields': (
                'satisfaccion_general',
                'satisfaccion_tamano',
                'satisfaccion_distribucion',
                'satisfaccion_ubicacion'
            ),
            'classes': ('wide',)
        }),
        ('Necesidades y Reparaciones', {
            'fields': (
                'requiere_reparaciones',
                'detalle_reparaciones',
                'requiere_mejoras',
                'detalle_mejoras'
            ),
            'classes': ('collapse',)
        }),
        ('Seguimiento Social', {
            'fields': (
                'adaptacion_familiar',
                'integracion_comunitaria',
                'conoce_vecinos',
                'participa_organizaciones'
            ),
            'classes': ('collapse',)
        }),
        ('Acceso a Servicios', {
            'fields': (
                'acceso_salud',
                'acceso_educacion',
                'acceso_transporte',
                'acceso_comercio'
            ),
            'classes': ('collapse',)
        }),
        ('Observaciones', {
            'fields': (
                'observaciones_tecnicas',
                'observaciones_sociales',
                'recomendaciones'
            ),
            'classes': ('wide',)
        }),
        ('Seguimiento', {
            'fields': (
                'requiere_seguimiento',
                'fecha_proximo_seguimiento'
            )
        }),
        ('Puntajes Calculados', {
            'fields': (
                'puntaje_habitabilidad',
                'puntaje_satisfaccion',
                'puntaje_social',
                'servicios_funcionando'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': (
                'fecha_creacion',
                'fecha_actualizacion',
                'actualizada_por'
            ),
            'classes': ('collapse',)
        })
    )
    
    inlines = [ArchivoFichaInline, HistorialFichaInline]
    
    def save_model(self, request, obj, form, change):
        if change:  # Si se está editando
            obj.actualizada_por = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'vivienda__proyecto',
            'evaluador',
            'actualizada_por'
        )


@admin.register(HistorialFicha)
class HistorialFichaAdmin(admin.ModelAdmin):
    list_display = (
        'ficha',
        'campo_modificado',
        'usuario',
        'fecha_cambio'
    )
    
    list_filter = (
        'fecha_cambio',
        'campo_modificado',
        'usuario'
    )
    
    search_fields = (
        'ficha__vivienda__codigo',
        'ficha__vivienda__proyecto__codigo',
        'campo_modificado',
        'usuario__nombre'
    )
    
    readonly_fields = ('fecha_cambio',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'ficha__vivienda__proyecto',
            'usuario'
        )


@admin.register(ArchivoFicha)
class ArchivoFichaAdmin(admin.ModelAdmin):
    list_display = (
        'ficha',
        'tipo',
        'descripcion',
        'fecha_subida',
        'subido_por'
    )
    
    list_filter = (
        'tipo',
        'fecha_subida',
        'subido_por'
    )
    
    search_fields = (
        'ficha__vivienda__codigo',
        'ficha__vivienda__proyecto__codigo',
        'descripcion'
    )
    
    readonly_fields = ('fecha_subida',)
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.subido_por = request.user
        super().save_model(request, obj, form, change)
