"""
Decoradores para control de acceso basado en roles
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden

def rol_requerido(*roles_permitidos):
    """
    Decorador que verifica si el usuario tiene uno de los roles permitidos.
    
    Uso:
        @rol_requerido('ADMINISTRADOR', 'TECHO')
        def mi_vista(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Debes iniciar sesión para acceder a esta página.')
                return redirect('login')
            
            # Superusuarios o miembros del grupo ADMINISTRADOR tienen acceso completo
            if request.user.is_superuser or request.user.groups.filter(name='ADMINISTRADOR').exists():
                return view_func(request, *args, **kwargs)
            
            # Verificar si tiene rol asignado
            if not request.user.rol:
                messages.error(request, 'Tu usuario no tiene un rol asignado. Contacta al administrador.')
                return redirect('dashboard')
            
            # Verificar si el rol está en los permitidos
            if request.user.rol.nombre not in roles_permitidos:
                messages.error(request, 'No tienes permisos para acceder a esta página.')
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def puede_ver_proyecto(view_func):
    """
    Decorador que verifica si el usuario puede ver un proyecto específico.
    - ADMINISTRADOR y TECHO: todos los proyectos
    - SERVIU: todos los proyectos (solo lectura)
    - CONSTRUCTORA: solo sus proyectos
    - FAMILIA: solo proyectos donde tienen vivienda asignada
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.is_superuser or request.user.groups.filter(name='ADMINISTRADOR').exists():
            return view_func(request, *args, **kwargs)
        
        if not request.user.rol:
            messages.error(request, 'Tu usuario no tiene un rol asignado.')
            return redirect('dashboard')
        
        rol = request.user.rol.nombre
        
        # ADMIN y TECHO tienen acceso completo
        if rol in ['ADMINISTRADOR', 'TECHO']:
            return view_func(request, *args, **kwargs)
        
        # SERVIU tiene acceso de lectura
        if rol == 'SERVIU':
            return view_func(request, *args, **kwargs)
        
        # Para CONSTRUCTORA y FAMILIA, verificar en la vista
        # (se implementa lógica específica en cada vista)
        return view_func(request, *args, **kwargs)
    
    return wrapper


def puede_editar_proyecto(view_func):
    """
    Decorador que verifica si el usuario puede editar un proyecto.
    - ADMINISTRADOR y TECHO: pueden editar
    - Otros: no pueden editar
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.is_superuser or request.user.groups.filter(name='ADMINISTRADOR').exists():
            return view_func(request, *args, **kwargs)
        
        if not request.user.rol:
            messages.error(request, 'Tu usuario no tiene un rol asignado.')
            return redirect('dashboard')
        
        rol = request.user.rol.nombre
        
        if rol not in ['ADMINISTRADOR', 'TECHO']:
            messages.error(request, 'No tienes permisos para editar proyectos.')
            return redirect('proyectos:lista')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def puede_crear_observacion(view_func):
    """
    Decorador que verifica si el usuario puede crear observaciones.
    - ADMINISTRADOR, TECHO, FAMILIA: pueden crear
    - CONSTRUCTORA: solo puede responder (no crear)
    - SERVIU: solo lectura
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.is_superuser or request.user.groups.filter(name='ADMINISTRADOR').exists():
            return view_func(request, *args, **kwargs)
        
        if not request.user.rol:
            messages.error(request, 'Tu usuario no tiene un rol asignado.')
            return redirect('dashboard')
        
        rol = request.user.rol.nombre
        
        if rol not in ['ADMINISTRADOR', 'TECHO', 'FAMILIA']:
            messages.error(request, 'No tienes permisos para crear observaciones.')
            return redirect('incidencias:lista_observaciones')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def puede_editar_observacion(view_func):
    """
    Decorador que verifica si el usuario puede editar observaciones.
    - ADMINISTRADOR y TECHO: pueden editar todas
    - CONSTRUCTORA: puede agregar soluciones y cerrar
    - FAMILIA: solo sus propias observaciones
    - SERVIU: solo lectura
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Solo ADMINISTRADOR, TECHO y CONSTRUCTORA (grupo) permiten editar observaciones
        if request.user.is_superuser or \
           request.user.groups.filter(name='ADMINISTRADOR').exists() or \
           request.user.groups.filter(name='TECHO').exists() or \
           request.user.groups.filter(name='CONSTRUCTORA').exists():
            return view_func(request, *args, **kwargs)
        messages.error(request, 'No tienes permisos para editar observaciones.')
        return redirect('incidencias:lista_observaciones')
    
    return wrapper


def puede_ver_reportes(view_func):
    """
    Decorador que verifica si el usuario puede ver reportes.
    - ADMINISTRADOR, TECHO, SERVIU: todos los reportes
    - CONSTRUCTORA: solo reportes de sus proyectos
    - FAMILIA: solo ficha de postventa de su vivienda
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Solo ADMINISTRADOR, TECHO y SERVIU permiten ver reportes
        if request.user.is_superuser or \
           request.user.groups.filter(name='ADMINISTRADOR').exists() or \
           request.user.groups.filter(name='TECHO').exists() or \
           request.user.groups.filter(name='SERVIU').exists():
            return view_func(request, *args, **kwargs)
        messages.error(request, 'No tienes permisos para ver reportes.')
        return redirect('dashboard')
    
    return wrapper
