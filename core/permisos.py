"""
Funciones auxiliares para verificar permisos por rol
"""

def tiene_rol(usuario, *roles):
    """
    Verifica si el usuario tiene uno de los roles especificados.
    
    Args:
        usuario: Objeto Usuario
        *roles: Lista de roles permitidos (ej: 'ADMINISTRADOR', 'TECHO')
    
    Returns:
        bool: True si el usuario tiene uno de los roles
    """
    if not usuario.is_authenticated:
        return False
    
    if usuario.is_superuser:
        return True
    
    if not usuario.rol:
        return False
    
    return usuario.rol.nombre in roles


def puede_ver_proyecto(usuario, proyecto):
    """
    Verifica si el usuario puede ver un proyecto específico.
    
    Returns:
        bool: True si puede ver el proyecto
    """
    if not usuario.is_authenticated:
        return False
    
    if usuario.is_superuser:
        return True
    
    if not usuario.rol:
        return False
    
    rol = usuario.rol.nombre
    
    # ADMIN, TECHO y SERVIU ven todos los proyectos
    if rol in ['ADMINISTRADOR', 'TECHO', 'SERVIU']:
        return True
    
    # CONSTRUCTORA solo ve sus proyectos
    if rol == 'CONSTRUCTORA':
        if usuario.empresa:
            return proyecto.constructora.nombre.lower() == usuario.empresa.lower()
        return False
    
    # FAMILIA solo ve proyectos donde tiene vivienda
    if rol == 'FAMILIA':
        return proyecto.vivienda_set.filter(beneficiario__icontains=usuario.nombre).exists()
    
    return False


def puede_editar_proyecto(usuario, proyecto):
    """
    Verifica si el usuario puede editar un proyecto.
    
    Returns:
        bool: True si puede editar el proyecto
    """
    if not usuario.is_authenticated:
        return False
    
    if usuario.is_superuser:
        return True
    
    if not usuario.rol:
        return False
    
    rol = usuario.rol.nombre
    
    # Solo ADMIN y TECHO pueden editar proyectos
    return rol in ['ADMINISTRADOR', 'TECHO']


def puede_ver_observacion(usuario, observacion):
    """
    Verifica si el usuario puede ver una observación específica.
    
    Returns:
        bool: True si puede ver la observación
    """
    # Usuarios no autenticados no pueden ver
    if not usuario.is_authenticated:
        return False
    # Superusuario tiene acceso completo
    if usuario.is_superuser:
        return True
    # ADMINISTRADOR, TECHO y SERVIU pueden ver todas
    if usuario.groups.filter(name__in=['ADMINISTRADOR', 'TECHO', 'SERVIU']).exists():
        return True
    # CONSTRUCTORA solo ve observaciones de sus proyectos
    if usuario.groups.filter(name='CONSTRUCTORA').exists():
        if usuario.empresa:
            proj_const = observacion.vivienda.proyecto.constructora.lower()
            return proj_const == usuario.empresa.lower()
        return False
    # FAMILIA solo ve sus propias observaciones (grupo o rol antiguo)
    is_familia = usuario.groups.filter(name='FAMILIA').exists() or (
        hasattr(usuario, 'rol') and usuario.rol and usuario.rol.nombre == 'FAMILIA'
    )
    if is_familia:
        benef = getattr(observacion.vivienda, 'beneficiario', None)
        if benef:
            if usuario.rut and getattr(benef, 'rut', None):
                return usuario.rut == benef.rut
            # Fallback: comparar nombres
            nombre_b = f"{benef.nombre} {benef.apellido_paterno}".strip().lower()
            return usuario.nombre.lower() in nombre_b
        return False
    # Otros no tienen acceso
    return False


def puede_editar_observacion(usuario, observacion):
    """
    Verifica si el usuario puede editar una observación.
    
    Returns:
        bool: True si puede editar la observación
    """
    if not usuario.is_authenticated:
        return False
    
    if usuario.is_superuser:
        return True
    
    if not usuario.rol:
        return False
    
    rol = usuario.rol.nombre
    
    # ADMIN y TECHO pueden editar todas
    if rol in ['ADMINISTRADOR', 'TECHO']:
        return True
    
    # SERVIU solo lectura
    if rol == 'SERVIU':
        return False
    
    # CONSTRUCTORA puede agregar soluciones y cerrar (verificar en vista)
    if rol == 'CONSTRUCTORA':
        if usuario.empresa:
            return observacion.vivienda.proyecto.constructora.nombre.lower() == usuario.empresa.lower()
        return False
    
    # FAMILIA puede editar sus propias observaciones si están abiertas
    if rol == 'FAMILIA':
        if observacion.estado.nombre == 'CERRADA':  # Cambiar a estado.nombre ya que estado es objeto
            return False
        # Verificar por RUT si existe, sino por nombre
        if hasattr(observacion.vivienda, 'beneficiario') and observacion.vivienda.beneficiario:
            if usuario.rut and observacion.vivienda.beneficiario.rut:
                return usuario.rut == observacion.vivienda.beneficiario.rut
            else:
                # Fallback: comparar nombres
                beneficiario_nombre = f"{observacion.vivienda.beneficiario.nombre} {observacion.vivienda.beneficiario.apellido_paterno}".lower()
                return usuario.nombre.lower() in beneficiario_nombre
        return False
    
    return False


def puede_crear_observacion(usuario, vivienda=None):
    """
    Verifica si el usuario puede crear observaciones.
    Si se proporciona vivienda, verifica si puede crear en esa vivienda específica.
    
    Returns:
        bool: True si puede crear observaciones
    """
    if not usuario.is_authenticated:
        return False
    
    if usuario.is_superuser:
        return True
    
    if not usuario.rol:
        return False
    
    rol = usuario.rol.nombre
    
    # ADMIN y TECHO pueden crear en cualquier vivienda
    if rol in ['ADMINISTRADOR', 'TECHO']:
        return True
    
    # SERVIU y CONSTRUCTORA no pueden crear observaciones
    if rol in ['SERVIU', 'CONSTRUCTORA']:
        return False
    
    # FAMILIA solo puede crear en su propia vivienda
    if rol == 'FAMILIA':
        if vivienda:
            return vivienda.beneficiario and usuario.nombre.lower() in vivienda.beneficiario.lower()
        return True  # Si no se especifica vivienda, permitir acceso al formulario
    
    return False


def puede_eliminar_observacion(usuario, observacion):
    """
    Verifica si el usuario puede eliminar una observación.
    
    Returns:
        bool: True si puede eliminar la observación
    """
    if not usuario.is_authenticated:
        return False
    
    if usuario.is_superuser:
        return True
    
    if not usuario.rol:
        return False
    
    rol = usuario.rol.nombre
    
    # Solo ADMIN y TECHO pueden eliminar
    return rol in ['ADMINISTRADOR', 'TECHO']


def puede_acceder_panel_maestro(usuario):
    """
    Verifica si el usuario puede acceder al panel maestro.
    
    Returns:
        bool: True si puede acceder al panel maestro
    """
    if not usuario.is_authenticated:
        return False
    
    if usuario.is_superuser:
        return True
    
    if not usuario.rol:
        return False
    
    # Solo ADMIN y TECHO acceden al panel maestro
    return usuario.rol.nombre in ['ADMINISTRADOR', 'TECHO']


def puede_ver_reporte(usuario, tipo_reporte, proyecto=None, vivienda=None):
    """
    Verifica si el usuario puede ver un tipo específico de reporte.
    
    Args:
        usuario: Objeto Usuario
        tipo_reporte: 'lista', 'acta', 'postventa', 'cierre'
        proyecto: Objeto Proyecto (opcional)
        vivienda: Objeto Vivienda (opcional)
    
    Returns:
        bool: True si puede ver el reporte
    """
    if not usuario.is_authenticated:
        return False
    
    if usuario.is_superuser:
        return True
    
    if not usuario.rol:
        return False
    
    rol = usuario.rol.nombre
    
    # ADMIN, TECHO y SERVIU ven todos los reportes
    if rol in ['ADMINISTRADOR', 'TECHO', 'SERVIU']:
        return True
    
    # CONSTRUCTORA ve reportes de sus proyectos
    if rol == 'CONSTRUCTORA':
        if tipo_reporte == 'postventa' and vivienda:
            if usuario.empresa:
                return vivienda.proyecto.constructora.nombre.lower() == usuario.empresa.lower()
        elif proyecto:
            if usuario.empresa:
                return proyecto.constructora.nombre.lower() == usuario.empresa.lower()
        return False
    
    # FAMILIA solo ve ficha de postventa de su vivienda
    if rol == 'FAMILIA':
        if tipo_reporte == 'postventa' and vivienda:
            return vivienda.beneficiario and usuario.nombre.lower() in vivienda.beneficiario.lower()
        # FAMILIA no puede ver otros tipos de reportes
        return False
    
    return False


def filtrar_proyectos_por_rol(usuario, queryset):
    """
    Filtra el queryset de proyectos según el rol del usuario.
    
    Args:
        usuario: Objeto Usuario
        queryset: QuerySet de Proyecto
    
    Returns:
        QuerySet filtrado
    """
    if not usuario.is_authenticated:
        return queryset.none()
    
    if usuario.is_superuser:
        return queryset
    
    if not usuario.rol:
        return queryset.none()
    
    rol = usuario.rol.nombre
    
    # ADMIN, TECHO y SERVIU ven todos
    if rol in ['ADMINISTRADOR', 'TECHO', 'SERVIU']:
        return queryset
    
    # CONSTRUCTORA solo sus proyectos
    if rol == 'CONSTRUCTORA' and usuario.empresa:
        return queryset.filter(constructora__iexact=usuario.empresa)
    
    # FAMILIA solo proyectos donde tiene vivienda - buscar por RUT (más preciso)
    if rol == 'FAMILIA':
        if usuario.rut:
            # Búsqueda exacta por RUT (más confiable)
            return queryset.filter(viviendas__beneficiario__rut=usuario.rut).distinct()
        else:
            # Fallback: buscar por nombre si no tiene RUT (usuarios antiguos)
            from django.db.models import Q
            return queryset.filter(
                Q(viviendas__beneficiario__nombre__icontains=usuario.nombre) |
                Q(viviendas__beneficiario__apellido_paterno__icontains=usuario.nombre) |
                Q(viviendas__familia_beneficiaria__icontains=usuario.nombre)
            ).distinct()
    
    return queryset.none()


def filtrar_observaciones_por_rol(usuario, queryset):
    """
    Filtra el queryset de observaciones según el rol del usuario.
    
    Args:
        usuario: Objeto Usuario
        queryset: QuerySet de Observacion
    
    Returns:
        QuerySet filtrado
    """
    # No autenticados no ven nada
    if not usuario.is_authenticated:
        return queryset.none()
    # Superusuario y roles ADMINISTRADOR, TECHO, SERVIU ven todo
    if usuario.is_superuser or usuario.groups.filter(name__in=['ADMINISTRADOR', 'TECHO', 'SERVIU']).exists():
        return queryset
    # CONSTRUCTORA solo observa sus proyectos
    if usuario.groups.filter(name='CONSTRUCTORA').exists() and getattr(usuario, 'empresa', None):
        return queryset.filter(vivienda__proyecto__constructora__iexact=usuario.empresa)
    # FAMILIA solo ve sus propias observaciones (por grupo o rol antiguo)
    is_familia = usuario.groups.filter(name='FAMILIA').exists() or (hasattr(usuario, 'rol') and usuario.rol and usuario.rol.nombre == 'FAMILIA')
    if is_familia:
        from django.db.models import Q
        # Combinar filtros por RUT y nombre/familia_beneficiaria
        filtros = Q()
        if getattr(usuario, 'rut', None):
            filtros |= Q(vivienda__beneficiario__rut=usuario.rut)
        filtros |= Q(vivienda__beneficiario__nombre__icontains=usuario.nombre)
        filtros |= Q(vivienda__beneficiario__apellido_paterno__icontains=usuario.nombre)
        filtros |= Q(vivienda__familia_beneficiaria__icontains=usuario.nombre)
        return queryset.filter(filtros)
    # Otros roles no ven observaciones
    return queryset.none()
