from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string

from .models import FichaPostventa, ArchivoFicha, HistorialFicha
from .forms import FichaPostventaForm, FiltroFichasForm, ArchivoFichaForm, BusquedaFichasForm
from proyectos.models import Vivienda, Proyecto
from core.decorators import rol_requerido
from core.models import Usuario
from weasyprint import HTML

import json


@login_required
def dashboard_fichas(request):
    """
    Dashboard principal con estadísticas y resumen de fichas
    """
    # Estadísticas generales
    total_fichas = FichaPostventa.objects.filter(activa=True).count()
    fichas_recientes = FichaPostventa.objects.filter(
        activa=True,
        fecha_creacion__gte=timezone.now().date() - timezone.timedelta(days=30)
    ).count()
    
    fichas_seguimiento = FichaPostventa.objects.filter(
        activa=True,
        requiere_seguimiento=True
    ).count()
    
    # Promedios de evaluación
    promedios = FichaPostventa.objects.filter(activa=True).aggregate(
        prom_habitabilidad=Avg('estado_general_vivienda'),
        prom_satisfaccion=Avg('satisfaccion_general')
    )
    
    # Fichas que requieren atención
    fichas_atencion = FichaPostventa.objects.filter(
        activa=True,
        requiere_seguimiento=True,
        fecha_proximo_seguimiento__lte=timezone.now().date() + timezone.timedelta(days=7)
    ).select_related('vivienda__proyecto', 'evaluador')[:10]
    
    # Proyectos con más fichas
    proyectos_stats = (FichaPostventa.objects
                      .filter(activa=True)
                      .values('vivienda__proyecto__nombre', 'vivienda__proyecto__codigo')
                      .annotate(total_fichas=Count('id'))
                      .order_by('-total_fichas')[:5])
    
    context = {
        'total_fichas': total_fichas,
        'fichas_recientes': fichas_recientes,
        'fichas_seguimiento': fichas_seguimiento,
        'promedio_habitabilidad': round(promedios.get('prom_habitabilidad', 0), 1),
        'promedio_satisfaccion': round(promedios.get('prom_satisfaccion', 0), 1),
        'fichas_atencion': fichas_atencion,
        'proyectos_stats': proyectos_stats,
    }
    
    return render(request, 'ficha_postventa/dashboard.html', context)


@login_required
def listar_fichas(request):
    """
    Lista todas las fichas con filtros y búsqueda
    """
    fichas = FichaPostventa.objects.filter(activa=True).select_related(
        'vivienda__proyecto',
        'evaluador'
    ).order_by('-fecha_creacion')
    
    # Aplicar filtros
    form_filtro = FiltroFichasForm(request.GET)
    form_busqueda = BusquedaFichasForm(request.GET)
    
    if form_filtro.is_valid():
        if form_filtro.cleaned_data.get('proyecto'):
            fichas = fichas.filter(vivienda__proyecto=form_filtro.cleaned_data['proyecto'])
        
        if form_filtro.cleaned_data.get('evaluador'):
            fichas = fichas.filter(evaluador=form_filtro.cleaned_data['evaluador'])
        
        if form_filtro.cleaned_data.get('fecha_desde'):
            fichas = fichas.filter(fecha_evaluacion__gte=form_filtro.cleaned_data['fecha_desde'])
        
        if form_filtro.cleaned_data.get('fecha_hasta'):
            fichas = fichas.filter(fecha_evaluacion__lte=form_filtro.cleaned_data['fecha_hasta'])
        
        if form_filtro.cleaned_data.get('requiere_seguimiento'):
            fichas = fichas.filter(requiere_seguimiento=True)
        
        if form_filtro.cleaned_data.get('estado_minimo'):
            fichas = fichas.filter(estado_general_vivienda__gte=int(form_filtro.cleaned_data['estado_minimo']))
    
    # Aplicar búsqueda
    if form_busqueda.is_valid():
        termino = form_busqueda.cleaned_data.get('termino')
        if termino:
            fichas = fichas.filter(
                Q(vivienda__codigo__icontains=termino) |
                Q(vivienda__proyecto__codigo__icontains=termino) |
                Q(vivienda__proyecto__nombre__icontains=termino) |
                Q(vivienda__familia_beneficiaria__icontains=termino) |
                Q(evaluador__nombre__icontains=termino)
            )
    
    # Paginación
    paginator = Paginator(fichas, 20)  # 20 fichas por página
    page = request.GET.get('page')
    fichas_page = paginator.get_page(page)
    
    context = {
        'fichas': fichas_page,
        'form_filtro': form_filtro,
        'form_busqueda': form_busqueda,
        'total_fichas': fichas.count()
    }
    
    return render(request, 'ficha_postventa/listar.html', context)


@login_required
@rol_requerido(['TECHO', 'ADMINISTRADOR'])
def crear_ficha(request):
    """
    Crear nueva ficha de postventa - solo TECHO y ADMINISTRADOR
    """
    if request.method == 'POST':
        form = FichaPostventaForm(request.POST, request=request)
        if form.is_valid():
            ficha = form.save(commit=False)
            # El evaluador se establece automáticamente en el formulario
            ficha.save()
            
            messages.success(request, f'Ficha de postventa creada exitosamente para {ficha.vivienda}')
            return redirect('ficha_postventa:detalle', pk=ficha.pk)
    else:
        form = FichaPostventaForm(request=request)
    
    context = {
        'form': form,
        'titulo': 'Crear Nueva Ficha de Postventa',
        'accion': 'Crear'
    }
    
    return render(request, 'ficha_postventa/crear_editar.html', context)


@login_required
def ver_ficha(request, pk):
    """
    Ver detalle de una ficha de postventa
    """
    ficha = get_object_or_404(
        FichaPostventa.objects.select_related('vivienda__proyecto', 'evaluador'),
        pk=pk,
        activa=True
    )
    
    # Verificar permisos - todos pueden ver, pero según su rol
    user_rol = request.user.rol.nombre if hasattr(request.user, 'rol') and request.user.rol else None
    puede_editar = user_rol in ['TECHO', 'ADMINISTRADOR']
    
    # Obtener archivos adjuntos
    archivos = ficha.archivos.all().order_by('-fecha_subida')
    
    # Obtener historial reciente
    historial = ficha.historial.all().order_by('-fecha_cambio')[:10]
    
    context = {
        'ficha': ficha,
        'puede_editar': puede_editar,
        'archivos': archivos,
        'historial': historial,
    }
    
    return render(request, 'ficha_postventa/detalle.html', context)


@login_required
@rol_requerido(['TECHO', 'ADMINISTRADOR'])
def editar_ficha(request, pk):
    """
    Editar ficha de postventa existente - solo TECHO y ADMINISTRADOR
    """
    ficha = get_object_or_404(FichaPostventa, pk=pk, activa=True)
    
    if request.method == 'POST':
        form = FichaPostventaForm(request.POST, instance=ficha, request=request)
        if form.is_valid():
            # Registrar cambios en el historial
            campos_modificados = []
            for field in form.changed_data:
                valor_anterior = getattr(ficha, field, None)
                campos_modificados.append((field, valor_anterior))
            
            ficha_actualizada = form.save(commit=False)
            ficha_actualizada.actualizada_por = request.user
            ficha_actualizada.save()
            
            # Crear registros de historial
            for field, valor_anterior in campos_modificados:
                valor_nuevo = getattr(ficha_actualizada, field, None)
                HistorialFicha.objects.create(
                    ficha=ficha_actualizada,
                    usuario=request.user,
                    campo_modificado=field,
                    valor_anterior=str(valor_anterior) if valor_anterior is not None else '',
                    valor_nuevo=str(valor_nuevo) if valor_nuevo is not None else ''
                )
            
            messages.success(request, f'Ficha de {ficha.vivienda} actualizada exitosamente')
            return redirect('ficha_postventa:detalle', pk=ficha.pk)
    else:
        form = FichaPostventaForm(instance=ficha, request=request)
    
    context = {
        'form': form,
        'ficha': ficha,
        'titulo': f'Editar Ficha - {ficha.vivienda}',
        'accion': 'Actualizar'
    }
    
    return render(request, 'ficha_postventa/crear_editar.html', context)


@login_required
@rol_requerido(['TECHO', 'ADMINISTRADOR'])
def eliminar_ficha(request, pk):
    """
    Desactivar ficha (eliminación lógica) - solo TECHO y ADMINISTRADOR
    """
    ficha = get_object_or_404(FichaPostventa, pk=pk, activa=True)
    
    if request.method == 'POST':
        ficha.activa = False
        ficha.actualizada_por = request.user
        ficha.save()
        
        # Registrar en historial
        HistorialFicha.objects.create(
            ficha=ficha,
            usuario=request.user,
            campo_modificado='activa',
            valor_anterior='True',
            valor_nuevo='False',
            observaciones='Ficha desactivada por el usuario'
        )
        
        messages.success(request, f'Ficha de {ficha.vivienda} desactivada exitosamente')
        return redirect('ficha_postventa:listar')
    
    context = {
        'ficha': ficha,
        'titulo': f'Confirmar Desactivación - {ficha.vivienda}'
    }
    
    return render(request, 'ficha_postventa/confirmar_eliminar.html', context)


@login_required
def ajax_viviendas_por_proyecto(request):
    """
    AJAX endpoint para obtener viviendas por proyecto
    """
    proyecto_id = request.GET.get('proyecto_id')
    
    if not proyecto_id:
        return JsonResponse({'viviendas': []})
    
    try:
        viviendas = Vivienda.objects.filter(
            proyecto_id=proyecto_id,
            activa=True,
            estado__in=['entregada', 'postventa']
        ).values('id', 'codigo', 'familia_beneficiaria').order_by('codigo')
        
        viviendas_data = [
            {
                'id': v['id'],
                'codigo': v['codigo'],
                'display': f"Vivienda {v['codigo']}" + (f" - {v['familia_beneficiaria']}" if v['familia_beneficiaria'] else "")
            }
            for v in viviendas
        ]
        
        return JsonResponse({'viviendas': viviendas_data})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@rol_requerido(['TECHO', 'ADMINISTRADOR'])
def subir_archivo(request, ficha_pk):
    """
    Subir archivo adjunto a una ficha
    """
    ficha = get_object_or_404(FichaPostventa, pk=ficha_pk, activa=True)
    
    if request.method == 'POST':
        form = ArchivoFichaForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = form.save(commit=False)
            archivo.ficha = ficha
            archivo.subido_por = request.user
            archivo.save()
            
            messages.success(request, 'Archivo subido exitosamente')
            return redirect('ficha_postventa:detalle', pk=ficha.pk)
    else:
        form = ArchivoFichaForm()
    
    context = {
        'form': form,
        'ficha': ficha,
        'titulo': f'Subir Archivo - {ficha.vivienda}'
    }
    
    return render(request, 'ficha_postventa/subir_archivo.html', context)


@login_required
@require_http_methods(["GET"])
def generar_pdf(request, pk):
    """
    Generar PDF de la ficha de postventa usando WeasyPrint
    """
    ficha = get_object_or_404(FichaPostventa, pk=pk, activa=True)
    # Renderizar el template HTML para PDF
    html_string = render_to_string('ficha_postventa/pdf_template.html', {'ficha': ficha})
    # Generar PDF
    html = HTML(string=html_string, base_url=request.build_absolute_uri(request.path))
    pdf_file = html.write_pdf()
    # Crear respuesta con PDF
    response = HttpResponse(pdf_file, content_type='application/pdf')
    # Establecer Content-Disposition
    if request.GET.get('download'):
        dispo = 'attachment'
    else:
        dispo = 'inline'
    filename = f'ficha_postventa_{ficha.pk}.pdf'
    response['Content-Disposition'] = f'{dispo}; filename="{filename}"'
    return response


@login_required
def estadisticas_proyecto(request, proyecto_pk):
    """
    Estadísticas de fichas por proyecto
    """
    proyecto = get_object_or_404(Proyecto, pk=proyecto_pk)
    
    fichas = FichaPostventa.objects.filter(
        vivienda__proyecto=proyecto,
        activa=True
    )
    
    # Estadísticas básicas
    total_fichas = fichas.count()
    total_viviendas = proyecto.viviendas.filter(activa=True).count()
    cobertura = (total_fichas / total_viviendas * 100) if total_viviendas > 0 else 0
    
    # Promedios
    stats = fichas.aggregate(
        prom_habitabilidad=Avg('estado_general_vivienda'),
        prom_satisfaccion=Avg('satisfaccion_general'),
        prom_social=Avg('adaptacion_familiar'),
        fichas_seguimiento=Count('id', filter=Q(requiere_seguimiento=True))
    )
    
    context = {
        'proyecto': proyecto,
        'total_fichas': total_fichas,
        'total_viviendas': total_viviendas,
        'cobertura': round(cobertura, 1),
        'promedio_habitabilidad': round(stats.get('prom_habitabilidad', 0), 1),
        'promedio_satisfaccion': round(stats.get('prom_satisfaccion', 0), 1),
        'promedio_social': round(stats.get('prom_social', 0), 1),
        'fichas_seguimiento': stats.get('fichas_seguimiento', 0),
        'fichas': fichas.select_related('vivienda', 'evaluador')
    }
    
    return render(request, 'ficha_postventa/estadisticas_proyecto.html', context)


@login_required
def ajax_buscar_beneficiario(request):
    """
    Busca un beneficiario por RUT y devuelve sus datos y viviendas asociadas
    """
    rut = request.GET.get('rut', '').strip()
    
    if not rut:
        return JsonResponse({'error': 'RUT no proporcionado'}, status=400)
    
    try:
        from proyectos.models import Beneficiario
        
        # Buscar beneficiario por RUT
        beneficiario = Beneficiario.objects.filter(rut=rut, activo=True).first()
        
        if not beneficiario:
            return JsonResponse({
                'found': False,
                'message': 'No se encontró un beneficiario con ese RUT'
            })
        
        # Obtener vivienda asociada
        vivienda = None
        if hasattr(beneficiario, 'vivienda') and beneficiario.vivienda:
            vivienda = beneficiario.vivienda
            vivienda_data = {
                'id': vivienda.id,
                'codigo': vivienda.codigo,
                'proyecto': vivienda.proyecto.nombre,
                'proyecto_id': vivienda.proyecto.id
            }
        else:
            vivienda_data = None
        
        # Obtener teléfonos
        telefonos = list(beneficiario.telefonos.filter(activo=True).values_list('numero', flat=True))
        
        return JsonResponse({
            'found': True,
            'beneficiario': {
                'nombre': beneficiario.nombre,
                'apellido_paterno': beneficiario.apellido_paterno,
                'apellido_materno': beneficiario.apellido_materno or '',
                'nombre_completo': beneficiario.nombre_completo,
                'email': beneficiario.email or '',
                'telefonos': telefonos
            },
            'vivienda': vivienda_data
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error al buscar beneficiario: {str(e)}'
        }, status=500)

