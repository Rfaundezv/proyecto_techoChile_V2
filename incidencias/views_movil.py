# Vista móvil optimizada para observaciones
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
import json

from .models import Observacion, EstadoObservacion, SeguimientoObservacion, TipoObservacion
from proyectos.models import Proyecto, Vivienda
from core.permisos import filtrar_observaciones_por_rol, puede_ver_observacion, puede_editar_observacion

@login_required
def observaciones_movil(request):
    """Vista principal móvil para observaciones - solo HTML básico"""
    # Obtener filtros básicos
    proyecto_id = request.GET.get('proyecto')
    estado_id = request.GET.get('estado')
    
    # Datos iniciales mínimos
    proyectos = Proyecto.objects.filter(activo=True).values('id', 'codigo', 'nombre')[:20]
    estados = EstadoObservacion.objects.filter(activo=True).values('id', 'nombre', 'codigo')
    
    context = {
        'proyectos': list(proyectos),
        'estados': list(estados),
        'proyecto_seleccionado': proyecto_id,
        'estado_seleccionado': estado_id,
        'es_movil': True
    }
    
    return render(request, 'incidencias/observaciones_movil.html', context)

@login_required
def observaciones_api_movil(request):
    """API ligera para cargar observaciones en móvil"""
    try:
        # Parámetros de paginación
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        # Filtros básicos
        proyecto_id = request.GET.get('proyecto')
        estado_id = request.GET.get('estado')
        buscar = request.GET.get('q', '').strip()
        urgente = request.GET.get('urgente')
        
        # Query base optimizado - solo campos necesarios
        observaciones = Observacion.objects.select_related(
            'vivienda__proyecto', 'estado', 'creado_por'
        ).filter(activo=True)
        
        # Aplicar permisos por rol
        observaciones = filtrar_observaciones_por_rol(request.user, observaciones)
        
        # Aplicar filtros
        if proyecto_id:
            observaciones = observaciones.filter(vivienda__proyecto_id=proyecto_id)
        if estado_id:
            observaciones = observaciones.filter(estado_id=estado_id)
        if urgente == 'true':
            observaciones = observaciones.filter(es_urgente=True)
        if buscar:
            observaciones = observaciones.filter(
                Q(elemento__icontains=buscar) |
                Q(detalle__icontains=buscar) |
                Q(vivienda__codigo__icontains=buscar)
            )
        
        # Ordenar por fecha más reciente
        observaciones = observaciones.order_by('-fecha_creacion')
        
        # Paginación
        paginator = Paginator(observaciones, per_page)
        page_obj = paginator.get_page(page)
        
        # Serializar datos mínimos
        observaciones_data = []
        for obs in page_obj:
            # Obtener archivos adjuntos
            archivos = obs.archivos_adjuntos.all()[:3]  # Solo primeros 3 archivos para performance
            archivos_data = []
            for archivo in archivos:
                archivos_data.append({
                    'id': archivo.id,
                    'nombre': archivo.nombre_original,
                    'url': archivo.archivo.url if archivo.archivo else None,
                    'tipo': archivo.archivo.name.split('.')[-1].lower() if archivo.archivo else 'unknown',
                    'tamaño': archivo.archivo.size if archivo.archivo else 0
                })
            
            # Obtener seguimientos/comentarios recientes (últimos 3 para móvil)
            seguimientos = obs.seguimientos.select_related('usuario').order_by('-fecha')[:3]
            comentarios_data = []
            for seg in seguimientos:
                comentarios_data.append({
                    'id': seg.id,
                    'accion': seg.accion,
                    'comentario': seg.comentario,
                    'fecha': seg.fecha.strftime('%d/%m/%Y %H:%M'),
                    'usuario': seg.usuario.nombre if seg.usuario else 'Sistema'
                })
            
            observaciones_data.append({
                'id': obs.id,
                'elemento': obs.elemento,
                'detalle': obs.detalle[:100] + '...' if len(obs.detalle) > 100 else obs.detalle,
                'vivienda_codigo': obs.vivienda.codigo,
                'proyecto_codigo': obs.vivienda.proyecto.codigo,
                'estado': {
                    'id': obs.estado.id,
                    'nombre': obs.estado.nombre,
                    'codigo': obs.estado.codigo
                },
                'prioridad': obs.prioridad,
                'es_urgente': obs.es_urgente,
                'fecha_creacion': obs.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
                'creado_por': obs.creado_por.nombre if obs.creado_por else 'Sistema',
                'puede_editar': puede_editar_observacion(request.user, obs),
                'esta_vencida': obs.esta_vencida if hasattr(obs, 'esta_vencida') else False,
                'total_archivos': obs.archivos_adjuntos.count(),
                'archivos': archivos_data,
                'total_comentarios': obs.seguimientos.count(),
                'comentarios': comentarios_data
            })
        
        return JsonResponse({
            'observaciones': observaciones_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'total_items': paginator.count
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_http_methods(["POST"])
def cambiar_estado_movil(request, observacion_id):
    """Cambio rápido de estado desde móvil"""
    try:
        data = json.loads(request.body)
        observacion = get_object_or_404(Observacion, id=observacion_id)
        
        if not puede_editar_observacion(request.user, observacion):
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        nuevo_estado_id = data.get('estado_id')
        comentario = data.get('comentario', '').strip()
        
        if not nuevo_estado_id:
            return JsonResponse({'error': 'Estado requerido'}, status=400)
        
        nuevo_estado = get_object_or_404(EstadoObservacion, id=nuevo_estado_id)
        estado_anterior = observacion.estado
        
        # Actualizar observación
        observacion.estado = nuevo_estado
        observacion.save()
        
        # Crear seguimiento
        SeguimientoObservacion.objects.create(
            observacion=observacion,
            usuario=request.user,
            accion=f'Cambio de estado (móvil)',
            comentario=comentario,
            estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado
        )
        
        return JsonResponse({
            'success': True,
            'nuevo_estado': {
                'id': nuevo_estado.id,
                'nombre': nuevo_estado.nombre,
                'codigo': nuevo_estado.codigo
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def actualizar_descripcion_movil(request, observacion_id):
    """Actualizar descripción desde móvil"""
    try:
        data = json.loads(request.body)
        observacion = get_object_or_404(Observacion, id=observacion_id)
        
        if not puede_editar_observacion(request.user, observacion):
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        nueva_descripcion = data.get('descripcion', '').strip()
        
        if not nueva_descripcion:
            return JsonResponse({'error': 'Descripción requerida'}, status=400)
        
        descripcion_anterior = observacion.detalle
        observacion.detalle = nueva_descripcion
        observacion.save()
        
        # Crear seguimiento
        SeguimientoObservacion.objects.create(
            observacion=observacion,
            usuario=request.user,
            accion='Descripción actualizada (móvil)',
            comentario=f'Descripción anterior: {descripcion_anterior[:100]}...' if len(descripcion_anterior) > 100 else f'Descripción anterior: {descripcion_anterior}'
        )
        
        return JsonResponse({
            'success': True,
            'nueva_descripcion': nueva_descripcion
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def obtener_descripcion_completa(request, observacion_id):
    """Obtener la descripción completa de una observación"""
    try:
        observacion = get_object_or_404(Observacion, id=observacion_id)
        
        if not puede_ver_observacion(request.user, observacion):
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        return JsonResponse({
            'success': True,
            'descripcion_completa': observacion.detalle
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def subir_archivo_movil(request, observacion_id):
    """Subir archivo desde móvil"""
    try:
        observacion = get_object_or_404(Observacion, id=observacion_id)
        
        if not puede_editar_observacion(request.user, observacion):
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        if 'archivo' not in request.FILES:
            return JsonResponse({'error': 'No se encontró archivo'}, status=400)
        
        archivo = request.FILES['archivo']
        descripcion = request.POST.get('descripcion', '').strip()
        
        # Validar tamaño (máximo 10MB)
        if archivo.size > 10 * 1024 * 1024:
            return JsonResponse({'error': 'Archivo muy grande (máximo 10MB)'}, status=400)
        
        # Validar tipo de archivo
        tipos_permitidos = ['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx', 'txt']
        extension = archivo.name.split('.')[-1].lower() if '.' in archivo.name else ''
        
        if extension not in tipos_permitidos:
            return JsonResponse({'error': 'Tipo de archivo no permitido'}, status=400)
        
        # Crear archivo adjunto
        from .models import ArchivoAdjuntoObservacion
        archivo_adjunto = ArchivoAdjuntoObservacion.objects.create(
            observacion=observacion,
            archivo=archivo,
            nombre_original=archivo.name,
            descripcion=descripcion,
            subido_por=request.user
        )
        
        # Crear seguimiento
        SeguimientoObservacion.objects.create(
            observacion=observacion,
            usuario=request.user,
            accion='Archivo agregado (móvil)',
            comentario=f'Archivo: {archivo.name}' + (f' - {descripcion}' if descripcion else '')
        )
        
        return JsonResponse({
            'success': True,
            'archivo': {
                'id': archivo_adjunto.id,
                'nombre': archivo_adjunto.nombre_original,
                'url': archivo_adjunto.archivo.url,
                'descripcion': archivo_adjunto.descripcion
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def observacion_detalle_movil(request, observacion_id):
    """Vista de detalle móvil ligera"""
    observacion = get_object_or_404(Observacion, id=observacion_id)
    
    if not puede_ver_observacion(request.user, observacion):
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    # Seguimientos recientes (últimos 5)
    seguimientos = observacion.seguimientos.select_related('usuario').order_by('-fecha')[:5]
    
    # Estados disponibles
    estados = EstadoObservacion.objects.filter(activo=True).values('id', 'nombre', 'codigo')
    
    context = {
        'observacion': observacion,
        'seguimientos': seguimientos,
        'estados': list(estados),
        'puede_editar': puede_editar_observacion(request.user, observacion),
        'es_movil': True
    }
    
    return render(request, 'incidencias/observacion_detalle_movil.html', context)

@login_required
@require_http_methods(["POST"])
def agregar_comentario_movil(request, observacion_id):
    """Agregar comentario/seguimiento desde móvil"""
    try:
        data = json.loads(request.body)
        observacion = get_object_or_404(Observacion, id=observacion_id)
        
        if not puede_editar_observacion(request.user, observacion):
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        comentario = data.get('comentario', '').strip()
        
        if not comentario:
            return JsonResponse({'error': 'El comentario no puede estar vacío'}, status=400)
        
        # Crear seguimiento
        seguimiento = SeguimientoObservacion.objects.create(
            observacion=observacion,
            usuario=request.user,
            accion='Comentario (móvil)',
            comentario=comentario
        )
        
        return JsonResponse({
            'success': True,
            'comentario': {
                'id': seguimiento.id,
                'accion': seguimiento.accion,
                'comentario': seguimiento.comentario,
                'fecha': seguimiento.fecha.strftime('%d/%m/%Y %H:%M'),
                'usuario': seguimiento.usuario.nombre if seguimiento.usuario else 'Sistema'
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def obtener_comentarios_movil(request, observacion_id):
    """Obtener todos los comentarios de una observación"""
    try:
        observacion = get_object_or_404(Observacion, id=observacion_id)
        
        if not puede_ver_observacion(request.user, observacion):
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        # Obtener todos los seguimientos
        seguimientos = observacion.seguimientos.select_related('usuario').order_by('-fecha')
        
        comentarios_data = []
        for seg in seguimientos:
            comentarios_data.append({
                'id': seg.id,
                'accion': seg.accion,
                'comentario': seg.comentario,
                'fecha': seg.fecha.strftime('%d/%m/%Y %H:%M'),
                'usuario': seg.usuario.nombre if seg.usuario else 'Sistema',
                'estado_anterior': seg.estado_anterior.nombre if seg.estado_anterior else None,
                'estado_nuevo': seg.estado_nuevo.nombre if seg.estado_nuevo else None
            })
        
        return JsonResponse({
            'success': True,
            'comentarios': comentarios_data,
            'total': len(comentarios_data)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def crear_observacion_movil(request):
    """Vista móvil optimizada para crear observaciones"""
    from .forms import ObservacionForm
    from .models import ArchivoAdjuntoObservacion
    from proyectos.models import Vivienda, Recinto, Proyecto
    from core.decorators import puede_crear_observacion
    from core.permisos import puede_crear_observacion as puede_crear_obs_func
    from django.contrib import messages
    from django.shortcuts import redirect
    from datetime import timedelta, date
    
    # Los administradores y TECHO siempre pueden seleccionar proyecto y vivienda
    es_admin_o_techo = (
        request.user.is_superuser or 
        request.user.groups.filter(name='ADMINISTRADOR').exists() or
        (hasattr(request.user, 'rol') and request.user.rol and request.user.rol.nombre in ['ADMINISTRADOR', 'TECHO'])
    )
    
    # Solo es familia si pertenece al grupo FAMILIA Y NO es admin/techo
    es_familia = (
        not es_admin_o_techo and 
        (request.user.groups.filter(name='FAMILIA').exists() or (
            hasattr(request.user, 'rol') and request.user.rol and request.user.rol.nombre == 'FAMILIA'
        ))
    )
    
    # Si es familia Y NO es admin/techo, usar lógica especial
    if es_familia and not es_admin_o_techo:
        # Buscar vivienda por RUT (más preciso) o por nombre (fallback)
        if request.user.rut:
            mi_vivienda = Vivienda.objects.filter(beneficiario__rut=request.user.rut).first()
        else:
            mi_vivienda = Vivienda.objects.filter(
                Q(beneficiario__nombre__icontains=request.user.nombre) |
                Q(beneficiario__apellido_paterno__icontains=request.user.nombre) |
                Q(familia_beneficiaria__icontains=request.user.nombre)
            ).first()
        
        # Si NO tiene vivienda asignada, mostrar error
        if not mi_vivienda:
            if request.method == 'POST':
                return JsonResponse({
                    'success': False,
                    'error': 'No se encontró una vivienda asignada para tu cuenta. Por favor contacta con el administrador.'
                })
            else:
                messages.error(
                    request, 
                    'No se encontró una vivienda asignada para tu cuenta. '
                    'Por favor contacta con el administrador para que te asigne una vivienda.'
                )
                return redirect('incidencias:observaciones_movil')
        
        # Si SÍ tiene vivienda, continuar con formulario precargado
        if request.method == 'POST':
            # Procesar datos JSON o FormData
            if request.content_type == 'application/json':
                try:
                    data = json.loads(request.body)
                except json.JSONDecodeError:
                    return JsonResponse({'success': False, 'error': 'Datos JSON inválidos'})
            else:
                data = request.POST
                
            form = ObservacionForm(data, request.FILES, exclude_fields=['proyecto', 'vivienda'])
            form.fields['recinto'].queryset = Recinto.objects.filter(activo=True)
            
            if form.is_valid():
                observacion = form.save(commit=False)
                observacion.creado_por = request.user
                observacion.vivienda = mi_vivienda  # Forzar su vivienda
                observacion.proyecto = mi_vivienda.proyecto  # Forzar su proyecto
                
                # Sincronizar es_urgente con prioridad
                if observacion.es_urgente:
                    observacion.prioridad = 'urgente'
                    
                # Asignar estado inicial
                try:
                    estado_abierta = EstadoObservacion.objects.get(codigo=1)
                except EstadoObservacion.DoesNotExist:
                    estado_abierta = EstadoObservacion.objects.filter(activo=True).first()
                
                if not estado_abierta:
                    return JsonResponse({
                        'success': False, 
                        'error': 'No se puede crear la observación: no hay estados configurados.'
                    })
                
                observacion.estado = estado_abierta
                
                # Asignar fecha de vencimiento automática
                try:
                    from core.models import ConfiguracionObservacion
                    config = ConfiguracionObservacion.get_configuracion()
                    if observacion.es_urgente:
                        dias_urgente = (config.horas_vencimiento_urgente + 23) // 24
                        observacion.fecha_vencimiento = date.today() + timedelta(days=dias_urgente)
                    else:
                        observacion.fecha_vencimiento = date.today() + timedelta(days=config.dias_vencimiento_normal)
                except:
                    # Valores por defecto si no hay configuración
                    if observacion.es_urgente:
                        observacion.fecha_vencimiento = date.today() + timedelta(days=2)
                    else:
                        observacion.fecha_vencimiento = date.today() + timedelta(days=120)
                
                observacion.save()
                
                # Procesar archivos adjuntos
                archivos_adjuntos = request.FILES.getlist('archivos_adjuntos')
                archivos_guardados = 0
                
                if archivos_adjuntos:
                    size_total = sum(archivo.size for archivo in archivos_adjuntos)
                    
                    if size_total <= 10 * 1024 * 1024:  # 10MB
                        for archivo in archivos_adjuntos:
                            try:
                                ArchivoAdjuntoObservacion.objects.create(
                                    observacion=observacion,
                                    archivo=archivo,
                                    nombre_original=archivo.name,
                                    subido_por=request.user
                                )
                                archivos_guardados += 1
                            except Exception:
                                pass
                
                # Crear seguimiento
                try:
                    comentario = 'Observación creada desde móvil por familia beneficiaria'
                    if archivos_guardados > 0:
                        comentario += f' con {archivos_guardados} archivo(s)'
                    
                    SeguimientoObservacion.objects.create(
                        observacion=observacion,
                        usuario=request.user,
                        accion='Creación',
                        comentario=comentario
                    )
                except:
                    pass
                
                return JsonResponse({
                    'success': True,
                    'message': 'Tu observación ha sido creada exitosamente.',
                    'observacion_id': observacion.pk,
                    'redirect_url': f'/incidencias/movil/detalle/{observacion.pk}/'
                })
            else:
                # Errores de formulario
                errors = {}
                for field, field_errors in form.errors.items():
                    errors[field] = [str(error) for error in field_errors]
                    
                return JsonResponse({
                    'success': False,
                    'errors': errors
                })
        else:
            # GET: Crear formulario con campos precargados para FAMILIA
            form = ObservacionForm(exclude_fields=['proyecto', 'vivienda'])
            form.fields['recinto'].queryset = Recinto.objects.filter(activo=True)
            
            context = {
                'form': form,
                'es_familia': True,
                'mi_vivienda': mi_vivienda,
                'es_movil': True,
                'proyectos': [{'id': mi_vivienda.proyecto.id, 'nombre': str(mi_vivienda.proyecto)}],
                'viviendas': [{'id': mi_vivienda.id, 'nombre': str(mi_vivienda)}],
                'recintos': list(Recinto.objects.filter(activo=True).values('id', 'nombre')),
                'tipos': list(TipoObservacion.objects.filter(activo=True).values('id', 'nombre')),
                'prioridades': Observacion.Prioridad.choices,
            }
            return render(request, 'incidencias/crear_observacion_movil.html', context)
    
    # **PARA ADMINISTRADORES, TECHO Y OTROS ROLES (pueden seleccionar proyecto y vivienda)**
    if request.method == 'POST':
        # Procesar datos JSON o FormData
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'error': 'Datos JSON inválidos'})
        else:
            data = request.POST
            
        form = ObservacionForm(data, request.FILES, user=request.user)
        
        # Permitir que el formulario valide con los datos del proyecto
        if 'proyecto' in data:
            try:
                proyecto_id = int(data.get('proyecto'))
                form.fields['vivienda'].queryset = Vivienda.objects.filter(proyecto_id=proyecto_id, activa=True)
            except (ValueError, TypeError):
                pass
        
        if form.is_valid():
            observacion = form.save(commit=False)
            observacion.creado_por = request.user
            
            # Asignar el proyecto desde el formulario
            if 'proyecto' in form.cleaned_data:
                observacion.proyecto = form.cleaned_data['proyecto']
            
            # Verificar permisos específicos para FAMILIA
            if request.user.groups.filter(name='FAMILIA').exists():
                vivienda = observacion.vivienda
                if not puede_crear_obs_func(request.user, vivienda):
                    return JsonResponse({
                        'success': False,
                        'error': 'No tienes permisos para crear observaciones en esta vivienda.'
                    })
            
            # Sincronizar es_urgente con prioridad
            if observacion.es_urgente:
                observacion.prioridad = 'urgente'
            elif observacion.prioridad == 'urgente':
                observacion.es_urgente = True
            
            # Asignar estado inicial
            try:
                estado_abierta = EstadoObservacion.objects.get(codigo=1)
            except EstadoObservacion.DoesNotExist:
                estado_abierta = EstadoObservacion.objects.filter(activo=True).first()
            
            if not estado_abierta:
                return JsonResponse({
                    'success': False,
                    'error': 'No se puede crear la observación: no hay estados configurados.'
                })
            
            observacion.estado = estado_abierta
            
            # Asignar fecha de vencimiento automática según configuración
            from core.models import ConfiguracionObservacion
            config = ConfiguracionObservacion.get_configuracion()
            if observacion.es_urgente:
                dias_urgente = (config.horas_vencimiento_urgente + 23) // 24  # 48h = 2 días
                observacion.fecha_vencimiento = date.today() + timedelta(days=dias_urgente)
            else:
                observacion.fecha_vencimiento = date.today() + timedelta(days=config.dias_vencimiento_normal)
            
            observacion.save()

            # Procesar archivos adjuntos
            archivos_adjuntos = request.FILES.getlist('archivos_adjuntos')
            archivos_guardados = 0
            size_total = sum(archivo.size for archivo in archivos_adjuntos)
            
            # Validar tamaño total (10MB)
            if size_total <= 10 * 1024 * 1024:
                for archivo in archivos_adjuntos:
                    try:
                        ArchivoAdjuntoObservacion.objects.create(
                            observacion=observacion,
                            archivo=archivo,
                            nombre_original=archivo.name,
                            subido_por=request.user
                        )
                        archivos_guardados += 1
                    except Exception:
                        pass

            # Crear seguimiento inicial
            comentario = 'Observación creada desde móvil'
            if archivos_guardados > 0:
                comentario += f' con {archivos_guardados} archivo(s) adicional(es)'
            
            try:
                SeguimientoObservacion.objects.create(
                    observacion=observacion,
                    usuario=request.user,
                    accion='Creación',
                    comentario=comentario
                )
            except:
                pass  # Si no existe el modelo de seguimiento, continuar

            return JsonResponse({
                'success': True,
                'message': 'Observación creada exitosamente.',
                'observacion_id': observacion.pk,
                'redirect_url': f'/incidencias/movil/detalle/{observacion.pk}/'
            })
        else:
            # Errores de formulario
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = [str(error) for error in field_errors]
                
            return JsonResponse({
                'success': False,
                'errors': errors
            })
    else:
        # GET: Formulario para administradores y otros roles
        form = ObservacionForm(user=request.user)
        
        # Datos para dropdowns
        proyectos = list(Proyecto.objects.filter(activo=True).values('id', 'codigo', 'nombre'))
        estados = list(EstadoObservacion.objects.filter(activo=True).values('id', 'nombre', 'codigo'))
        recintos = list(Recinto.objects.filter(activo=True).values('id', 'nombre'))
        
        context = {
            'form': form,
            'es_familia': es_familia,
            'es_movil': True,
            'proyectos': proyectos,
            'estados': estados,
            'recintos': recintos,
            'tipos': list(TipoObservacion.objects.filter(activo=True).values('id', 'nombre')),
            'prioridades': Observacion.Prioridad.choices,
            'viviendas': []  # Se cargarán vía AJAX al seleccionar proyecto
        }
        return render(request, 'incidencias/crear_observacion_movil.html', context)