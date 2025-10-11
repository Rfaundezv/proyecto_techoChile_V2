from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Proyecto, Vivienda
from .forms import ProyectoForm, ViviendaForm, BeneficiarioForm
from core.decorators import puede_ver_proyecto, puede_editar_proyecto, rol_requerido
from core.permisos import (
    filtrar_proyectos_por_rol,
    puede_ver_proyecto as puede_ver_proyecto_func,
    puede_editar_proyecto as puede_editar_proyecto_func,
)

@login_required
@rol_requerido('ADMINISTRADOR', 'TECHO', 'SERVIU', 'CONSTRUCTORA')
def lista_proyectos(request):
    # Obtener todos los proyectos activos
    proyectos = Proyecto.objects.filter(activo=True).select_related('region', 'comuna', 'creado_por')
    
    # Filtrar proyectos según el rol del usuario
    proyectos = filtrar_proyectos_por_rol(request.user, proyectos)

    # Filtros de búsqueda
    search = request.GET.get('search')
    if search:
        proyectos = proyectos.filter(
            Q(codigo__icontains=search) | 
            Q(nombre__icontains=search) |
            Q(constructora__icontains=search)
        )

    paginator = Paginator(proyectos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'proyectos': page_obj,
        'search': search,
    }
    return render(request, 'proyectos/lista.html', context)

@login_required
@puede_editar_proyecto
def crear_proyecto(request):
    if request.method == 'POST':
        form = ProyectoForm(request.POST)
        if form.is_valid():
            proyecto = form.save(commit=False)
            proyecto.creado_por = request.user
            if form.cleaned_data.get('constructora'):
                proyecto.constructora = form.cleaned_data['constructora']
            proyecto.save()
            messages.success(request, f'Proyecto {proyecto.codigo} creado exitosamente.')
            return redirect('proyectos:detalle', pk=proyecto.pk)
    else:
        form = ProyectoForm()

    return render(request, 'proyectos/crear.html', {'form': form})

@login_required
@rol_requerido('ADMINISTRADOR', 'TECHO', 'SERVIU', 'CONSTRUCTORA')
def detalle_proyecto(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    
    # Verificar permisos de visualización
    if not puede_ver_proyecto_func(request.user, proyecto):
        messages.error(request, 'No tienes permisos para ver este proyecto.')
        return redirect('proyectos:lista')
    
    # Usar related_name definido en el modelo y ordenar por código de vivienda
    viviendas = proyecto.viviendas.all().order_by('codigo')

    context = {
        'proyecto': proyecto,
        'viviendas': viviendas,
        'puede_editar': puede_editar_proyecto_func(request.user, proyecto),
    }
    return render(request, 'proyectos/detalle.html', context)

@login_required
def editar_proyecto(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    
    # Verificar permisos de edición
    if not puede_editar_proyecto_func(request.user, proyecto):
        messages.error(request, 'No tienes permisos para editar este proyecto.')
        return redirect('proyectos:detalle', pk=proyecto.pk)
    
    if request.method == 'POST':
        form = ProyectoForm(request.POST, instance=proyecto)
        if form.is_valid():
            form.save()
            messages.success(request, f'Proyecto {proyecto.codigo} actualizado exitosamente.')
            return redirect('proyectos:detalle', pk=proyecto.pk)
    else:
        form = ProyectoForm(instance=proyecto)

    return render(request, 'proyectos/editar.html', {'form': form, 'proyecto': proyecto})

@login_required
def crear_vivienda(request, proyecto_pk):
    proyecto = get_object_or_404(Proyecto, pk=proyecto_pk)
    
    # Verificar permisos de edición (solo ADMIN y TECHO pueden crear viviendas)
    if not puede_editar_proyecto_func(request.user, proyecto):
        messages.error(request, 'No tienes permisos para crear viviendas en este proyecto.')
        return redirect('proyectos:detalle', pk=proyecto.pk)
    
    if request.method == 'POST':
        form = ViviendaForm(request.POST)
        if form.is_valid():
            vivienda = form.save(commit=False)
            vivienda.proyecto = proyecto
            vivienda.save()
            messages.success(request, f'Vivienda {vivienda.numero_vivienda} creada exitosamente.')
            return redirect('proyectos:detalle', pk=proyecto.pk)
    else:
        form = ViviendaForm()

    context = {
        'form': form,
        'proyecto': proyecto,
    }
    return render(request, 'proyectos/crear_vivienda.html', context)

@login_required
@rol_requerido('ADMINISTRADOR', 'TECHO')
def crear_beneficiario(request):
    if request.method == 'POST':
        form = BeneficiarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Beneficiario creado exitosamente.')
            return redirect('proyectos:lista') # Redirigir a la lista de proyectos
    else:
        form = BeneficiarioForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Nuevo Beneficiario'
    }
    return render(request, 'proyectos/crear_beneficiario.html', context)

@login_required
def buscar_beneficiario_por_rut(request):
    """Vista AJAX para buscar beneficiario por RUT"""
    from django.http import JsonResponse
    from .models import Beneficiario
    
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        rut_original = request.GET.get('rut', '').strip()
        
        if not rut_original:
            return JsonResponse({'error': 'RUT no proporcionado'}, status=400)
        
        # Limpiar RUT para la búsqueda: remover puntos y espacios
        rut_limpio = rut_original.replace('.', '').replace(' ', '')
        
        try:
            # Buscar beneficiario por RUT (con o sin puntos)
            beneficiario = Beneficiario.objects.filter(
                Q(rut=rut_original) | Q(rut=rut_limpio),
                activo=True
            ).first()
            
            if beneficiario:
                return JsonResponse({
                    'success': True,
                    'beneficiario': {
                        'id': beneficiario.id,
                        'nombre_completo': beneficiario.nombre_completo,
                        'nombre': beneficiario.nombre,
                        'apellido_paterno': beneficiario.apellido_paterno,
                        'apellido_materno': beneficiario.apellido_materno,
                        'email': beneficiario.email or ''
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'No se encontró un beneficiario con ese RUT'
                })
        except Exception as e:
            return JsonResponse({'error': 'Error en la búsqueda'}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)
