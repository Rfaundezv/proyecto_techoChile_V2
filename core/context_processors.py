from proyectos.models import Proyecto, Vivienda
from incidencias.models import Observacion
from core.permisos import (
    tiene_rol,
    puede_acceder_panel_maestro,
)

def global_stats_context(request):
    """
    Context processor para agregar estadísticas globales a todas las plantillas.
    Personalizado según el rol del usuario.
    """
    if request.user.is_authenticated:
        user = request.user
        
        # **CASO ESPECIAL PARA FAMILIA**
        if user.rol and user.rol.nombre == 'FAMILIA':
            # Solo mostrar estadísticas de SU vivienda
            try:
                from django.db.models import Q
                
                # Buscar viviendas del beneficiario
                mis_viviendas = Vivienda.objects.filter(
                    Q(beneficiario__nombre__icontains=user.nombre) |
                    Q(beneficiario__apellido_paterno__icontains=user.nombre) |
                    Q(familia_beneficiaria__icontains=user.nombre)
                )
                
                if mis_viviendas.exists():
                    mi_vivienda = mis_viviendas.first()
                    mis_observaciones = Observacion.objects.filter(vivienda=mi_vivienda)
                    
                    return {
                        'total_proyectos': 1,  # Solo su proyecto
                        'viviendas_total': 1,  # Solo su vivienda
                        'obs_total': mis_observaciones.count(),
                    }
            except:
                pass
            
            # Si no encuentra vivienda, mostrar 0
            return {
                'total_proyectos': 0,
                'viviendas_total': 0,
                'obs_total': 0,
            }
        
        # **CASO ESPECIAL PARA CONSTRUCTORA**
        if user.rol and user.rol.nombre == 'CONSTRUCTORA' and getattr(user, 'empresa', None):
            # Solo mostrar estadísticas de SU constructora
            try:
                empresa_usuario = user.empresa.strip().lower()
                
                # Proyectos de la constructora
                proyectos_constructora = Proyecto.objects.filter(
                    constructora__icontains=empresa_usuario
                )
                
                # Viviendas de esos proyectos
                viviendas_constructora = Vivienda.objects.filter(
                    proyecto__in=proyectos_constructora
                )
                
                # Observaciones de esas viviendas
                observaciones_constructora = Observacion.objects.filter(
                    vivienda__proyecto__constructora__icontains=empresa_usuario
                )
                
                return {
                    'total_proyectos': proyectos_constructora.count(),
                    'viviendas_total': viviendas_constructora.count(),
                    'obs_total': observaciones_constructora.count(),
                }
            except:
                pass
            
            # Si hay error, mostrar 0
            return {
                'total_proyectos': 0,
                'viviendas_total': 0,
                'obs_total': 0,
            }
        
        # **PARA OTROS ROLES**: Estadísticas globales
        total_proyectos = Proyecto.objects.count()
        viviendas_total = Vivienda.objects.count()
        obs_total = Observacion.objects.count()
        
        return {
            'total_proyectos': total_proyectos,
            'viviendas_total': viviendas_total,
            'obs_total': obs_total,
        }
    return {}


def permisos_usuario(request):
    """
    Agrega información de permisos del usuario actual a todos los templates.
    """
    if not request.user.is_authenticated:
        return {
            'es_admin': False,
            'es_techo': False,
            'es_serviu': False,
            'es_constructora': False,
            'es_familia': False,
            'puede_panel_maestro': False,
            'rol_usuario': None,
        }
    
    return {
        'es_admin': tiene_rol(request.user, 'ADMINISTRADOR'),
        'es_techo': tiene_rol(request.user, 'TECHO'),
        'es_serviu': tiene_rol(request.user, 'SERVIU'),
        'es_constructora': tiene_rol(request.user, 'CONSTRUCTORA'),
        'es_familia': tiene_rol(request.user, 'FAMILIA'),
        'puede_panel_maestro': puede_acceder_panel_maestro(request.user),
        'rol_usuario': request.user.rol.nombre if request.user.rol else None,
        'nombre_constructora': request.user.empresa if getattr(request.user, 'empresa', None) else None,
    }

