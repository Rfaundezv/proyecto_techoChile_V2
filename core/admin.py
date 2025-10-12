
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario, Rol, Region, Comuna, Constructora, ConfiguracionObservacion

@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    list_display = ('email', 'nombre', 'rol', 'constructora', 'region', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'rol', 'region', 'constructora')
    search_fields = ('email', 'nombre')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información personal', {'fields': ('nombre', 'telefono')}),
        ('Rol y Empresa', {'fields': ('rol', 'constructora', 'empresa')}),
        ('Ubicación', {'fields': ('region', 'comuna')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombre', 'password1', 'password2', 'rol', 'constructora', 'region'),
        }),
    )

    class Media:
        js = ('admin/js/usuario_admin.js',)

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo']
    list_filter = ['activo']

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre']
    search_fields = ['nombre', 'codigo']

@admin.register(Comuna)
class ComunaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'region', 'codigo']
    list_filter = ['region']
    search_fields = ['nombre']

@admin.register(Constructora)
class ConstructoraAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'rut', 'region', 'comuna', 'contacto', 'activo']
    list_filter = ['region', 'activo']
    search_fields = ['nombre', 'contacto', 'rut']


@admin.register(ConfiguracionObservacion)
class ConfiguracionObservacionAdmin(admin.ModelAdmin):
    list_display = ['dias_vencimiento_normal', 'horas_vencimiento_urgente', 'fecha_modificacion', 'modificado_por']
    readonly_fields = ['fecha_modificacion']
    
    def has_add_permission(self, request):
        # Solo permitir una instancia
        return not ConfiguracionObservacion.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # No permitir eliminar la configuración
        return False
