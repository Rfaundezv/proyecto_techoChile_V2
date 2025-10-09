
from django.contrib import admin
from .models import TipologiaVivienda, Proyecto, Recinto, Vivienda, Beneficiario, Telefono

@admin.register(TipologiaVivienda)
class TipologiaViviendaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'activa']
    list_filter = ['activa']
    search_fields = ['nombre', 'codigo']

@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'constructora', 'region', 'comuna', 'estado_postventa', 'activo']
    list_filter = ['activo', 'region', 'fecha_entrega']
    search_fields = ['codigo', 'nombre', 'constructora']
    date_hierarchy = 'fecha_entrega'

@admin.register(Recinto)
class RecintoAdmin(admin.ModelAdmin):
    list_display = ['tipologia', 'codigo', 'nombre', 'activo']
    list_filter = ['tipologia', 'activo']
    search_fields = ['nombre']

@admin.register(Vivienda)
class ViviendaAdmin(admin.ModelAdmin):
    list_display = ['proyecto', 'codigo', 'familia_beneficiaria', 'beneficiario', 'estado', 'fecha_entrega']
    list_filter = ['estado', 'proyecto', 'tipologia']
    search_fields = ['codigo', 'familia_beneficiaria', 'beneficiario__nombre']
    date_hierarchy = 'fecha_entrega'


class TelefonoInline(admin.TabularInline):
    model = Telefono
    extra = 1

@admin.register(Beneficiario)
class BeneficiarioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'rut', 'telefonos_list', 'email']
    search_fields = ['nombre', 'rut']
    inlines = [TelefonoInline]

    def telefonos_list(self, obj):
        return ", ".join(obj.telefonos.values_list('numero', flat=True))
    telefonos_list.short_description = 'Teléfonos'
