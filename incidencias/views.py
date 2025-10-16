from django.views.generic import View
from django.shortcuts import get_object_or_404, render
from .models import Observacion, ArchivoAdjuntoObservacion
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
# Vista para mostrar archivos adjuntos de una observación en incidencias
class ObservacionArchivosView(View):
    @method_decorator(login_required)
    def get(self, request, pk):
        observacion = get_object_or_404(Observacion, pk=pk)
        archivos = list(ArchivoAdjuntoObservacion.objects.filter(observacion=observacion))
        archivo_principal = None
        if observacion.archivo_adjunto:
            archivo_principal = observacion.archivo_adjunto
        return render(request, 'incidencias/observacion_archivos.html', {
            'observacion': observacion,
            'archivos': archivos,
            'archivo_principal': archivo_principal,
            'titulo': f"Archivos de Observación #{observacion.pk}"
        })
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone
from django import forms
from .models import Observacion, EstadoObservacion, SeguimientoObservacion, ArchivoAdjuntoObservacion
from .forms import FiltroObservacionForm, ObservacionForm, CambioEstadoForm, ArchivoAdjuntoForm
from proyectos.models import Vivienda, Recinto, Proyecto
from core.decorators import puede_crear_observacion, puede_editar_observacion
from core.permisos import (
    filtrar_observaciones_por_rol,
    puede_ver_observacion,
    puede_editar_observacion as puede_editar_obs_func,
    puede_crear_observacion as puede_crear_obs_func,
)

@login_required
def lista_observaciones(request):
    form = FiltroObservacionForm(request.GET, user=request.user)
    observaciones = Observacion.objects.select_related(
        'vivienda__proyecto', 'recinto', 'creado_por'
    ).prefetch_related('archivos_adjuntos').order_by('-fecha_creacion')
    
    # Filtrar observaciones según el rol del usuario (incluye rol antiguo)
    observaciones = filtrar_observaciones_por_rol(request.user, observaciones)
    # Determinar si el usuario es FAMILIA (grupo o rol antiguo)
    es_familia = request.user.groups.filter(name='FAMILIA').exists() or ( 
        hasattr(request.user, 'rol') and request.user.rol and request.user.rol.nombre == 'FAMILIA' 
    ) 
    # Si es familia, limitar a su propia vivienda
    mi_vivienda = None
    if es_familia:
        # Obtener vivienda del beneficiario por RUT o nombre
        if getattr(request.user, 'rut', None):
            mi_vivienda = Vivienda.objects.filter(beneficiario__rut=request.user.rut).first()
        else:
            mi_vivienda = Vivienda.objects.filter(
                Q(beneficiario__nombre__icontains=request.user.nombre) |
                Q(beneficiario__apellido_paterno__icontains=request.user.nombre) |
                Q(familia_beneficiaria__icontains=request.user.nombre)
            ).first()
        if mi_vivienda:
            observaciones = observaciones.filter(vivienda=mi_vivienda)

    # Filtros desde URL (para enlaces del dashboard)
    if request.GET.get('estado'):
        observaciones = observaciones.filter(estado=request.GET.get('estado'))
    
    if request.GET.get('es_urgente') == '1':
        observaciones = observaciones.filter(es_urgente=True)

    # Aplicar filtros del formulario
    if form.is_valid():
        if form.cleaned_data.get('proyecto'):
            observaciones = observaciones.filter(vivienda__proyecto=form.cleaned_data['proyecto'])

        if form.cleaned_data.get('numero_vivienda'):
            observaciones = observaciones.filter(
                vivienda__numero_vivienda__icontains=form.cleaned_data['numero_vivienda']
            )

        if form.cleaned_data.get('estado'):
            observaciones = observaciones.filter(estado=form.cleaned_data['estado'])

        if form.cleaned_data.get('tipo'):
            observaciones = observaciones.filter(tipo=form.cleaned_data['tipo'])

        if form.cleaned_data.get('buscar'):
            buscar = form.cleaned_data['buscar']
            observaciones = observaciones.filter(
                Q(elemento__icontains=buscar) |
                Q(descripcion__icontains=buscar) |
                Q(recinto__nombre__icontains=buscar)
            )

    # Paginación
    paginator = Paginator(observaciones, 15)
    page_number = request.GET.get('page')
    observaciones_pagina = paginator.get_page(page_number)

    # Agregar atributos calculados por elemento SOLO en la página actual (evitar iterar todo el queryset)
    from datetime import timedelta
    for obs in observaciones_pagina:
        # Total de archivos adjuntos (archivos adicionales + archivo principal si existe)
        total_adjuntos = obs.archivos_adjuntos.count()
        obs.total_archivos = total_adjuntos + (1 if obs.archivo_adjunto else 0)
        # Fallback de fecha de vencimiento si no existiera (para visualización)
        if not obs.fecha_vencimiento and obs.fecha_creacion:
            base_date = obs.fecha_creacion.date()
            if obs.es_urgente or obs.prioridad == 'URGENTE':
                obs.fecha_vencimiento = base_date + timedelta(days=2)  # 48 horas ≈ 2 días
            else:
                obs.fecha_vencimiento = base_date + timedelta(days=120)

    # Permiso para cambiar estado (solo no familias pueden cambiar)
    puede_cambiar = not es_familia
    # Métricas para familias
    if es_familia and mi_vivienda:
        obs_total = observaciones.count()
        obs_abiertas = observaciones.filter(estado__nombre='Abierta').count()
        obs_cerradas = observaciones.filter(estado__nombre='Cerrada').count()
        obs_urgentes = observaciones.filter(es_urgente=True, estado__nombre='Abierta').count()
        from datetime import date
        obs_vencidas = observaciones.filter(fecha_vencimiento__lt=date.today(), estado__nombre='Abierta').count()
    else:
        obs_total = observaciones.count()
        obs_abiertas = obs_cerradas = obs_urgentes = obs_vencidas = None

    # Estados permitidos para el cambio (solo si puede cambiar estado)
    if puede_cambiar:
        estados = EstadoObservacion.objects.filter(activo=True).order_by('nombre')
    else:
        estados = []

    context = {
        'form': form,
        'observaciones': observaciones_pagina,
        'titulo': 'Mis Observaciones' if es_familia else 'Observaciones',
        # Familias siempre pueden crear en su vivienda asignada
        'puede_crear': True if es_familia else puede_crear_obs_func(request.user),
        'es_familia': es_familia,
        'puede_cambiar_estado': puede_cambiar,
        'mi_vivienda': mi_vivienda,
        # Métricas para familias
        'obs_total': obs_total,
        'obs_abiertas': obs_abiertas,
        'obs_cerradas': obs_cerradas,
        'obs_urgentes': obs_urgentes,
        'obs_vencidas': obs_vencidas,
        'estados': estados,
    }
    return render(request, 'incidencias/lista_observaciones.html', context)

@login_required
@puede_crear_observacion
def crear_observacion(request):
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
        from django.db.models import Q
        
        # Buscar vivienda por RUT (más preciso) o por nombre (fallback)
        if request.user.rut:
            # Búsqueda exacta por RUT (más confiable)
            mi_vivienda = Vivienda.objects.filter(beneficiario__rut=request.user.rut).first()
        else:
            # Fallback: buscar por nombre si no tiene RUT (usuarios antiguos)
            mi_vivienda = Vivienda.objects.filter(
                Q(beneficiario__nombre__icontains=request.user.nombre) |
                Q(beneficiario__apellido_paterno__icontains=request.user.nombre) |
                Q(familia_beneficiaria__icontains=request.user.nombre)
            ).first()
        
        # Si NO tiene vivienda asignada, mostrar error
        if not mi_vivienda:
            messages.error(
                request, 
                'No se encontró una vivienda asignada para tu cuenta. '
                'Por favor contacta con el administrador para que te asigne una vivienda.'
            )
            return redirect('incidencias:lista_observaciones')
        
        # Si SÍ tiene vivienda, continuar con formulario precargado
        if request.method == 'POST':
            form = ObservacionForm(request.POST, request.FILES, exclude_fields=['proyecto', 'vivienda'])
            
            # Para familias, permitir todos los recintos activos
            form.fields['recinto'].queryset = Recinto.objects.filter(activo=True)
            
            # Debug: verificar si el form es válido
            if not form.is_valid():
                # Mostrar errores específicos
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'Error en {field}: {error}')
                # También mostrar datos enviados para debug
                messages.warning(request, f'Datos POST: {dict(request.POST)}')
                return render(request, 'incidencias/crear_observacion.html', {
                    'form': form,
                    'es_familia': True,
                    'mi_vivienda': mi_vivienda,
                })
            # Forzar la vivienda del usuario
            observacion = form.save(commit=False)
            observacion.creado_por = request.user
            observacion.vivienda = mi_vivienda  # Forzar su vivienda
            observacion.proyecto = mi_vivienda.proyecto  # Forzar su proyecto
            
            # Sincronizar es_urgente con prioridad
            if observacion.es_urgente:
                observacion.prioridad = Observacion.Prioridad.URGENTE
            try:
                estado_abierta = EstadoObservacion.objects.get(codigo=1)
            except EstadoObservacion.DoesNotExist:
                try:
                    estado_abierta = EstadoObservacion.objects.filter(activo=True).first()
                except:
                    estado_abierta = None
            
            if estado_abierta:
                observacion.estado = estado_abierta
            else:
                # Si no hay estados, no guardar
                messages.error(request, 'No se puede crear la observación: no hay estados configurados. Contacte al administrador.')
                return redirect('incidencias:lista_observaciones')
            
            # Asignar fecha de vencimiento automática
            from datetime import timedelta, date
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
                
                if size_total > 10 * 1024 * 1024:
                    messages.warning(request, f'Algunos archivos no se pudieron guardar (tamaño máximo 10MB)')
                else:
                    for archivo in archivos_adjuntos:
                        try:
                            ArchivoAdjuntoObservacion.objects.create(
                                observacion=observacion,
                                archivo=archivo,
                                nombre_original=archivo.name,
                                subido_por=request.user
                            )
                            archivos_guardados += 1
                        except Exception as e:
                            messages.warning(request, f'No se pudo guardar {archivo.name}')
            
            # Crear seguimiento
            try:
                comentario = 'Observación creada por familia beneficiaria'
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
            
            mensaje = 'Tu observación ha sido creada exitosamente. '
            mensaje += 'El equipo de TECHO revisará y dará seguimiento a tu solicitud.'
            messages.success(request, mensaje)
            return redirect('incidencias:detalle_observacion', pk=observacion.pk)
        else:
            # GET: Crear formulario con campos precargados para FAMILIA
            form = ObservacionForm(exclude_fields=['proyecto', 'vivienda'])
            
            # Filtrar recintos activos (sin filtrar por tipología para evitar problemas de validación)
            form.fields['recinto'].queryset = Recinto.objects.filter(activo=True)
        
        # Renderizar con contexto especial para FAMILIA
        context = {
            'form': form,
            'es_familia': True,
            'mi_vivienda': mi_vivienda,
        }
        return render(request, 'incidencias/crear_observacion.html', context)
    
    # **PARA ADMINISTRADORES, TECHO Y OTROS ROLES (pueden seleccionar proyecto y vivienda)**
    if request.method == 'POST':
        form = ObservacionForm(request.POST, request.FILES, user=request.user)
        
        # Permitir que el formulario valide con los datos del proyecto
        if 'proyecto' in request.POST:
            try:
                proyecto_id = int(request.POST.get('proyecto'))
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
                    messages.error(request, 'No tienes permisos para crear observaciones en esta vivienda.')
                    return redirect('incidencias:lista_observaciones')
            
            # Sincronizar es_urgente con prioridad
            if observacion.es_urgente:
                observacion.prioridad = Observacion.Prioridad.URGENTE
            elif observacion.prioridad == Observacion.Prioridad.URGENTE:
                observacion.es_urgente = True
            
            # Asignar estado inicial
            try:
                estado_abierta = EstadoObservacion.objects.get(codigo=1)
            except EstadoObservacion.DoesNotExist:
                try:
                    estado_abierta = EstadoObservacion.objects.filter(activo=True).first()
                except:
                    estado_abierta = None
            
            if estado_abierta:
                observacion.estado = estado_abierta
            else:
                messages.error(request, 'No se puede crear la observación: no hay estados configurados. Contacte al administrador.')
                return redirect('incidencias:lista_observaciones')
            
            # Asignar fecha de vencimiento automática según configuración
            from core.models import ConfiguracionObservacion
            from datetime import timedelta, date
            
            config = ConfiguracionObservacion.get_configuracion()
            if observacion.es_urgente:
                # Urgente: sumar horas configuradas (por defecto 48 horas)
                # Convertir horas a días (redondeando hacia arriba)
                dias_urgente = (config.horas_vencimiento_urgente + 23) // 24  # 48h = 2 días
                observacion.fecha_vencimiento = date.today() + timedelta(days=dias_urgente)
            else:
                # Normal: sumar días configurados (por defecto 120 días)
                observacion.fecha_vencimiento = date.today() + timedelta(days=config.dias_vencimiento_normal)
            
            observacion.save()

            # Procesar archivos adjuntos
            archivos_adjuntos = request.FILES.getlist('archivos_adjuntos')
            archivos_guardados = 0
            size_total = sum(archivo.size for archivo in archivos_adjuntos)
            
            # Validar tamaño total (10MB)
            if size_total > 10 * 1024 * 1024:
                messages.error(request, f'El tamaño total de los archivos ({size_total / (1024*1024):.2f} MB) excede el límite de 10MB')
            else:
                for archivo in archivos_adjuntos:
                    try:
                        ArchivoAdjuntoObservacion.objects.create(
                            observacion=observacion,
                            archivo=archivo,
                            nombre_original=archivo.name,
                            subido_por=request.user
                        )
                        archivos_guardados += 1
                    except Exception as e:
                        messages.warning(request, f'No se pudo guardar el archivo {archivo.name}: {str(e)}')

            # Crear seguimiento inicial (si existe el modelo)
            comentario = 'Observación creada'
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

            mensaje = 'Observación creada exitosamente.'
            if archivos_guardados > 0:
                mensaje += f' Se adjuntaron {archivos_guardados} archivo(s) adicional(es).'
            messages.success(request, mensaje)
            return redirect('incidencias:detalle_observacion', pk=observacion.pk)
    else:
        form = ObservacionForm(user=request.user)
        # Administradores y otros roles pueden seleccionar proyecto y vivienda
        if 'proyecto' in form.fields:
            form.fields['proyecto'].queryset = Proyecto.objects.filter(activo=True)
        if 'vivienda' in form.fields:
            form.fields['vivienda'].queryset = Vivienda.objects.none()  # Inicialmente vacío
        if 'recinto' in form.fields:
            form.fields['recinto'].queryset = Recinto.objects.filter(activo=True)
    
    # Pasar el contexto es_familia para que el template sepa qué mostrar
    context = {
        'form': form,
        'es_familia': es_familia
    }
    return render(request, 'incidencias/crear_observacion.html', context)
    
    # **PARA OTROS ROLES (ADMIN, TECHO, CONSTRUCTORA)**
    if request.method == 'POST':
        form = ObservacionForm(request.POST, request.FILES, user=request.user)
        
        # Permitir que el formulario valide con los datos del proyecto
        if 'proyecto' in request.POST:
            try:
                proyecto_id = int(request.POST.get('proyecto'))
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
                    messages.error(request, 'No tienes permisos para crear observaciones en esta vivienda.')
                    return redirect('incidencias:lista_observaciones')
            
            # Sincronizar es_urgente con prioridad
            if observacion.es_urgente:
                observacion.prioridad = Observacion.Prioridad.URGENTE
            elif observacion.prioridad == Observacion.Prioridad.URGENTE:
                observacion.es_urgente = True
            
            # Asignar estado inicial
            try:
                estado_abierta = EstadoObservacion.objects.get(codigo=1)
            except EstadoObservacion.DoesNotExist:
                try:
                    estado_abierta = EstadoObservacion.objects.filter(activo=True).first()
                except:
                    estado_abierta = None
            
            if estado_abierta:
                observacion.estado = estado_abierta
            else:
                messages.error(request, 'No se puede crear la observación: no hay estados configurados. Contacte al administrador.')
                return redirect('incidencias:lista_observaciones')
            
            # Asignar fecha de vencimiento automática según configuración
            from core.models import ConfiguracionObservacion
            from datetime import timedelta, date
            
            config = ConfiguracionObservacion.get_configuracion()
            if observacion.es_urgente:
                # Urgente: sumar horas configuradas (por defecto 48 horas)
                # Convertir horas a días (redondeando hacia arriba)
                dias_urgente = (config.horas_vencimiento_urgente + 23) // 24  # 48h = 2 días
                observacion.fecha_vencimiento = date.today() + timedelta(days=dias_urgente)
            else:
                # Normal: sumar días configurados (por defecto 120 días)
                observacion.fecha_vencimiento = date.today() + timedelta(days=config.dias_vencimiento_normal)
            
            observacion.save()

            # Procesar archivos adjuntos
            archivos_adjuntos = request.FILES.getlist('archivos_adjuntos')
            archivos_guardados = 0
            size_total = sum(archivo.size for archivo in archivos_adjuntos)
            
            # Validar tamaño total (10MB)
            if size_total > 10 * 1024 * 1024:
                messages.error(request, f'El tamaño total de los archivos ({size_total / (1024*1024):.2f} MB) excede el límite de 10MB')
            else:
                for archivo in archivos_adjuntos:
                    try:
                        ArchivoAdjuntoObservacion.objects.create(
                            observacion=observacion,
                            archivo=archivo,
                            nombre_original=archivo.name,
                            subido_por=request.user
                        )
                        archivos_guardados += 1
                    except Exception as e:
                        messages.warning(request, f'No se pudo guardar el archivo {archivo.name}: {str(e)}')

            # Crear seguimiento inicial (si existe el modelo)
            comentario = 'Observación creada'
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

            mensaje = 'Observación creada exitosamente.'
            if archivos_guardados > 0:
                mensaje += f' Se adjuntaron {archivos_guardados} archivo(s) adicional(es).'
            messages.success(request, mensaje)
            return redirect('incidencias:detalle_observacion', pk=observacion.pk)
    else:
        form = ObservacionForm(user=request.user)
        # Administradores y otros roles pueden seleccionar proyecto y vivienda
        # El queryset de proyecto ya está filtrado por el __init__ del formulario según el rol
        form.fields['vivienda'].queryset = Vivienda.objects.none()  # Inicialmente vacío
        form.fields['recinto'].queryset = Recinto.objects.filter(activo=True)
    
    return render(request, 'incidencias/crear_observacion.html', {'form': form, 'es_familia': es_familia})

@login_required
def detalle_observacion(request, pk):
    observacion = get_object_or_404(Observacion, pk=pk)
    
    # Verificar permisos de visualización
    if not puede_ver_observacion(request.user, observacion):
        messages.error(request, 'No tienes permisos para ver esta observación.')
        return redirect('incidencias:lista_observaciones')
    
    # Verificar permisos de edición
    puede_editar = puede_editar_obs_func(request.user, observacion)
    
    # Determinar qué acciones puede hacer según el rol
    puede_cambiar_estado = False
    puede_subir_archivos = False
    puede_agregar_solucion = False

    if request.user.rol:
        rol = request.user.rol.nombre
        if rol in ['ADMINISTRADOR', 'TECHO']:
            puede_cambiar_estado = True
            puede_subir_archivos = True
            puede_agregar_solucion = True
        elif rol == 'CONSTRUCTORA':
            puede_agregar_solucion = True
            # Permitir cambiar estado si está Abierta, En Proceso o Rechazada
            puede_cambiar_estado = observacion.estado.nombre in ['Abierta', 'En Proceso', 'Rechazada']
            puede_subir_archivos = True
        elif rol == 'FAMILIA':
            puede_subir_archivos = True if observacion.estado.nombre == 'Abierta' else False
    
    archivos = observacion.archivos_adjuntos.all().order_by('-fecha_subida')

    # Formulario para cambio de estado y subida de archivos
    if request.method == 'POST':
        # Verificar permisos de edición antes de procesar
        if not puede_editar:
            messages.error(request, 'No tienes permisos para modificar esta observación.')
            return redirect('incidencias:detalle_observacion', pk=pk)
        
        # Verificar si es cambio de estado o subida de archivo
        if 'cambiar_estado' in request.POST and puede_cambiar_estado:
            form = CambioEstadoForm(request.POST, estado_actual=observacion.estado)
            archivo_form = ArchivoAdjuntoForm()
            
            if form.is_valid():
                nuevo_estado = form.cleaned_data['estado']
                comentario = form.cleaned_data['comentario']

                # Guardar estado anterior
                estado_anterior = observacion.estado

                # Cambiar estado
                observacion.estado = nuevo_estado
                if nuevo_estado.nombre == 'Cerrada':
                    observacion.fecha_cierre = timezone.now()
                observacion.save()

                # Crear seguimiento
                SeguimientoObservacion.objects.create(
                    observacion=observacion,
                    usuario=request.user,
                    accion=f'Cambio de estado',
                    comentario=comentario,
                    estado_anterior=estado_anterior,
                    estado_nuevo=nuevo_estado
                )

                messages.success(request, f'Estado cambiado a "{nuevo_estado.nombre}" exitosamente.')
                return redirect('incidencias:detalle_observacion', pk=pk)
        
        elif 'subir_archivo' in request.POST:
            archivo_form = ArchivoAdjuntoForm(request.POST, request.FILES)
            form = CambioEstadoForm()
            
            if archivo_form.is_valid():
                archivo = archivo_form.save(commit=False)
                archivo.observacion = observacion
                archivo.subido_por = request.user
                archivo.save()
                
                # Crear seguimiento
                SeguimientoObservacion.objects.create(
                    observacion=observacion,
                    usuario=request.user,
                    accion='Archivo adjuntado',
                    comentario=f'Archivo: {archivo.nombre_original}'
                )
                
                messages.success(request, 'Archivo adjuntado exitosamente.')
                return redirect('incidencias:detalle_observacion', pk=pk)
    else:
        form = None
        archivo_form = None
        if puede_cambiar_estado:
            form = CambioEstadoForm(estado_actual=observacion.estado)
        if puede_subir_archivos:
            archivo_form = ArchivoAdjuntoForm()

    context = {
        'observacion': observacion,
        'archivos': archivos,
        'form': form,
        'archivo_form': archivo_form,
        'puede_editar': puede_editar,
        'puede_cambiar_estado': puede_cambiar_estado,
        'puede_subir_archivos': puede_subir_archivos,
        'puede_agregar_solucion': puede_agregar_solucion,
    }
    return render(request, 'incidencias/detalle_observacion.html', context)

@login_required
def cambiar_estado_observacion(request, pk):
    observacion = get_object_or_404(Observacion, pk=pk)

    if request.method == 'POST':
        nuevo_estado_id = request.POST.get('estado')
        comentario = request.POST.get('comentario', '')

        try:
            nuevo_estado = EstadoObservacion.objects.get(id=nuevo_estado_id)
            estado_anterior = observacion.estado

            # Cambiar estado
            observacion.estado = nuevo_estado
            if nuevo_estado.nombre == 'Cerrada':
                observacion.fecha_cierre = timezone.now()
            observacion.save()

            # Crear seguimiento con comentario
            SeguimientoObservacion.objects.create(
                observacion=observacion,
                usuario=request.user,
                accion=f'Cambio de estado: {estado_anterior.nombre} → {nuevo_estado.nombre}',
                comentario=comentario,
                estado_anterior=estado_anterior,
                estado_nuevo=nuevo_estado
            )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Estado cambiado a "{nuevo_estado.nombre}"',
                    'nuevo_estado': {
                        'id': nuevo_estado.id,
                        'nombre': nuevo_estado.nombre,
                        'badge_class': get_badge_class(nuevo_estado.nombre)
                    }
                })
            else:
                messages.success(request, f'Estado cambiado a "{nuevo_estado.nombre}" exitosamente.')
        except EstadoObservacion.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Estado no válido'})
            messages.error(request, 'Estado no válido')

    return redirect('incidencias:detalle_observacion', pk=pk)

def get_badge_class(estado_nombre):
    """Devuelve la clase CSS para el badge según el estado"""
    clases = {
        'Abierta': 'badge-abierta',
        'En Proceso': 'badge-proceso',
        'Cerrada': 'badge-cerrada',
        'Rechazada': 'badge-vencida'
    }
    return clases.get(estado_nombre, 'bg-secondary')

@login_required
def ajax_viviendas_por_proyecto(request):
    proyecto_id = request.GET.get('proyecto_id')
    viviendas = []
    
    if proyecto_id:
        try:
            # Filtrar solo viviendas activas
            viviendas_queryset = Vivienda.objects.filter(
                proyecto_id=proyecto_id, 
                activa=True
            ).order_by('codigo')
            
            viviendas = list(viviendas_queryset.values('id', 'codigo'))
            print(f"Viviendas encontradas para proyecto {proyecto_id}: {len(viviendas)}")
            
        except Exception as e:
            print(f"Error al obtener viviendas: {e}")
    
    return JsonResponse({'viviendas': viviendas})

@login_required
def ajax_recintos_por_proyecto(request):
    """DEPRECADO: Mantener por compatibilidad, pero usar ajax_recintos_por_vivienda"""
    proyecto_id = request.GET.get('proyecto_id')
    recintos = []
    if proyecto_id:
        try:
            tipologias = Vivienda.objects.filter(proyecto_id=proyecto_id).values_list('tipologia', flat=True).distinct()
            recintos = list(Recinto.objects.filter(tipologia__in=tipologias).values('id', 'nombre'))
        except Exception as e:
            pass
    return JsonResponse({'recintos': recintos})

@login_required
def ajax_recintos_por_vivienda(request):
    """Devuelve los recintos según la tipología de la vivienda seleccionada"""
    vivienda_id = request.GET.get('vivienda_id')
    recintos = []
    if vivienda_id:
        try:
            vivienda = Vivienda.objects.select_related('tipologia').get(id=vivienda_id)
            recintos = list(
                Recinto.objects.filter(tipologia=vivienda.tipologia)
                .values('id', 'nombre')
                .order_by('nombre')
            )
        except Vivienda.DoesNotExist:
            pass
        except Exception as e:
            pass
    return JsonResponse({'recintos': recintos})

@login_required
def ajax_elementos_por_recinto(request):
    """Devuelve los elementos disponibles de un recinto específico"""
    recinto_id = request.GET.get('recinto_id')
    elementos = []
    if recinto_id:
        try:
            recinto = Recinto.objects.get(id=recinto_id)
            # elementos_disponibles es un JSONField con una lista
            if recinto.elementos_disponibles:
                elementos = recinto.elementos_disponibles
        except Recinto.DoesNotExist:
            pass
        except Exception as e:
            pass
    return JsonResponse({'elementos': elementos})

@login_required
def eliminar_archivo_observacion(request, pk):
    """Elimina un archivo adjunto de una observación"""
    archivo = get_object_or_404(ArchivoAdjuntoObservacion, pk=pk)
    observacion_pk = archivo.observacion.pk
    
    # Verificar permisos (opcional: solo el que subió el archivo o admin puede eliminarlo)
    if request.user == archivo.subido_por or request.user.is_staff:
        nombre_archivo = archivo.nombre_original
        archivo.delete()
        
        # Crear seguimiento
        SeguimientoObservacion.objects.create(
            observacion_id=observacion_pk,
            usuario=request.user,
            accion='Archivo eliminado',
            comentario=f'Archivo eliminado: {nombre_archivo}'
        )
        
        messages.success(request, 'Archivo eliminado exitosamente.')
    else:
        messages.error(request, 'No tienes permiso para eliminar este archivo.')
    
    return redirect('incidencias:detalle_observacion', pk=observacion_pk)
