from incidencias.models import ArchivoAdjuntoObservacion
# Vista para mostrar archivos adjuntos de una observación en el panel maestro
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Count, Q, F, Func
from django.contrib import messages
from .models import Comuna, Region, Rol
from .decorators import rol_requerido, RolRequiredMixin
from proyectos.models import Proyecto, Vivienda
from incidencias.models import ArchivoAdjuntoObservacion, Observacion
from datetime import datetime, timedelta
import logging
from .models import Constructora, Usuario
from proyectos.models import Beneficiario

logger = logging.getLogger(__name__)

class ObservacionArchivosView(View):
    @method_decorator(login_required)
    def get(self, request, pk):
        observacion = get_object_or_404(Observacion, pk=pk)
        archivos = ArchivoAdjuntoObservacion.objects.filter(observacion=observacion)
        return render(request, 'maestro/observacion_archivos.html', {
            'observacion': observacion,
            'archivos': archivos,
            'titulo': f"Archivos de Observación #{observacion.pk}"
        })
@login_required
def dashboard(request):

    # --- Filtros desde GET ---
    region_id = request.GET.get('region')
    # estado_id = request.GET.get('estado')  # Eliminado filtro por estado
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # Listas para el filtro
    regiones = Region.objects.filter(activo=True).order_by('codigo')
    # from incidencias.models import EstadoObservacion
    # estados = list(EstadoObservacion.objects.filter(activo=True).values_list('id', 'nombre'))

    # Cumplimiento de plazos por constructora
    from core.utils.cumplimiento_constructora import get_cumplimiento_plazos_por_constructora
    cumplimiento_constructoras = get_cumplimiento_plazos_por_constructora(
        region_id=region_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )

    # Comunas de Valparaíso con viviendas (sin filtro)
    comuna_objs = []
    try:
        region_valpo = Region.objects.get(nombre__icontains='valparaiso')
        comunas_valpo = region_valpo.comunas.all()
        for comuna in comunas_valpo:
            total_viv = Vivienda.objects.filter(proyecto__comuna=comuna).count()
            if total_viv > 0:
                comuna_objs.append({'nombre': comuna.nombre, 'total_viviendas': total_viv})
    except Region.DoesNotExist:
        comuna_objs = []

    # --- Métricas por región (usando utilitario compartido) ---
    from core.utils.region_metrics import get_region_metrics
    metrics_region = get_region_metrics(region_id=region_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
    for region in metrics_region:
        region['estado'] = 'Bueno'  # Puedes agregar lógica de estado si lo necesitas

    # Determinar si el usuario es familia
    user = request.user
    es_familia = (
        user.groups.filter(name='FAMILIA').exists() or 
        (hasattr(user, 'rol') and user.rol and user.rol.nombre == 'FAMILIA')
    )
    mi_vivienda = None
    sin_vivienda = False
    proyectos_user = None
    # **CASO ESPECIAL PARA FAMILIA**
    if es_familia:
        # Buscar el beneficiario asociado al usuario por RUT
        beneficiario = Beneficiario.objects.filter(rut=user.rut).first() if user.rut else None
        mi_vivienda = Vivienda.objects.filter(beneficiario=beneficiario, activa=True).first() if beneficiario else None
        # Observaciones SOLO de su vivienda
        if mi_vivienda:
            mis_observaciones = Observacion.objects.filter(vivienda=mi_vivienda)
            obs_total = mis_observaciones.count()
            obs_abiertas = mis_observaciones.filter(estado__nombre='Abierta').count()
            obs_cerradas = mis_observaciones.filter(estado__nombre='Cerrada').count()
            obs_urgentes = mis_observaciones.filter(es_urgente=True, estado__nombre='Abierta').count()
            obs_vencidas = mis_observaciones.filter(fecha_vencimiento__lt=datetime.now().date(), estado__nombre='Abierta').count()
            ultimas_observaciones = mis_observaciones.select_related('vivienda__proyecto', 'vivienda', 'estado').order_by('-fecha_creacion')[:5]
        else:
            obs_total = obs_abiertas = obs_cerradas = obs_urgentes = obs_vencidas = 0
            ultimas_observaciones = []
        if obs_total > 0:
            porc_cerradas = round((obs_cerradas / obs_total) * 100, 1)
            porc_abiertas = round((obs_abiertas / obs_total) * 100, 1)
            porc_vencidas = round((obs_vencidas / obs_total) * 100, 1)
        else:
            porc_cerradas = porc_abiertas = porc_vencidas = 0
        viviendas_asignadas = 1 if mi_vivienda and mi_vivienda.beneficiario else 0
        total_proyectos = 1
        viviendas_total = 1
        viviendas_entregadas = 1 if mi_vivienda and mi_vivienda.estado == 'entregada' else 0
        is_admin = False
        sin_vivienda = mi_vivienda is None
    else:

        proyectos_qs = Proyecto.objects.all()
        if region_id:
            proyectos_qs = proyectos_qs.filter(region_id=region_id)
        # El modelo Proyecto no tiene campo 'estado', el filtro de estado debe aplicarse sobre Vivienda o Observacion
        # Solo filtrar por fechas en proyectos
        if fecha_inicio:
            proyectos_qs = proyectos_qs.filter(fecha_creacion__date__gte=fecha_inicio)
        if fecha_fin:
            proyectos_qs = proyectos_qs.filter(fecha_creacion__date__lte=fecha_fin)
        # Nunca filtrar proyectos por estado

        if user.is_superuser or (user.rol and user.rol.nombre == 'ADMINISTRADOR'):
            proyectos_user = proyectos_qs
        elif user.rol and user.rol.nombre == 'CONSTRUCTORA':
            if getattr(user, 'constructora', None):
                proyectos_user = proyectos_qs.filter(constructora=user.constructora)
            elif getattr(user, 'empresa', None):
                empresa_usuario = user.empresa.strip().lower()
                proyectos_user = proyectos_qs.filter(constructora__nombre__icontains=empresa_usuario)
            else:
                proyectos_user = Proyecto.objects.none()
        else:
            proyectos_user = proyectos_qs.filter(
                Q(creado_por=user) | 
                Q(region=user.region) if user.region else Q()
            ).distinct()
        if proyectos_user is not None:
            total_proyectos = proyectos_user.count()
            viviendas_total = Vivienda.objects.filter(proyecto__in=proyectos_user, activa=True).count()
            viviendas_entregadas = Vivienda.objects.filter(
                proyecto__in=proyectos_user, 
                estado='entregada'
            ).count()
            obs_qs = Observacion.objects.filter(vivienda__proyecto__in=proyectos_user)
            # if estado_id:
            #     obs_qs = obs_qs.filter(estado_id=estado_id)
            if fecha_inicio:
                obs_qs = obs_qs.filter(fecha_creacion__date__gte=fecha_inicio)
            if fecha_fin:
                obs_qs = obs_qs.filter(fecha_creacion__date__lte=fecha_fin)
            obs_total = obs_qs.count()
            obs_abiertas = obs_qs.filter(estado__nombre='Abierta').count()
            obs_cerradas = obs_qs.filter(estado__nombre='Cerrada').count()
            obs_urgentes = obs_qs.filter(es_urgente=True, estado__nombre='Abierta').count()
            obs_vencidas = obs_qs.filter(fecha_vencimiento__lt=datetime.now().date(), estado__nombre='Abierta').count()
            if obs_total > 0:
                porc_cerradas = round((obs_cerradas / obs_total) * 100, 1)
                porc_abiertas = round((obs_abiertas / obs_total) * 100, 1)
                porc_vencidas = round((obs_vencidas / obs_total) * 100, 1)
            else:
                porc_cerradas = porc_abiertas = porc_vencidas = 0
            ultimas_observaciones = obs_qs.select_related('vivienda__proyecto', 'vivienda', 'estado').order_by('-fecha_creacion')[:5]
            viviendas_asignadas = Vivienda.objects.filter(proyecto__in=proyectos_user, activa=True).exclude(beneficiario__isnull=True).count()
            is_admin = user.rol and user.rol.nombre == 'ADMINISTRADOR'
        else:
            total_proyectos = viviendas_total = viviendas_entregadas = obs_total = obs_abiertas = obs_cerradas = obs_urgentes = obs_vencidas = porc_cerradas = porc_abiertas = porc_vencidas = 0
            ultimas_observaciones = []
            viviendas_asignadas = 0
            is_admin = False

    # Datos para gráfico de observaciones por tipo
    if es_familia and mi_vivienda:
        datos_tipo = (
            Observacion.objects.filter(vivienda=mi_vivienda)
            .values('tipo__nombre')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
    else:
        if proyectos_user is not None:
            obs_tipo_qs = Observacion.objects.filter(vivienda__proyecto__in=proyectos_user)
            # if estado_id:
            #     obs_tipo_qs = obs_tipo_qs.filter(estado_id=estado_id)
            if fecha_inicio:
                obs_tipo_qs = obs_tipo_qs.filter(fecha_creacion__date__gte=fecha_inicio)
            if fecha_fin:
                obs_tipo_qs = obs_tipo_qs.filter(fecha_creacion__date__lte=fecha_fin)
            datos_tipo = (
                obs_tipo_qs
                .values('tipo__nombre')
                .annotate(total=Count('id'))
                .order_by('-total')
            )
        else:
            datos_tipo = []
    labels = [d['tipo__nombre'] for d in datos_tipo]
    values = [d['total'] for d in datos_tipo]

    # --- Agregación de casos cerrados por mes ---
    from django.db.models.functions import TruncMonth
    if es_familia and mi_vivienda:
        cerradas_qs = Observacion.objects.filter(vivienda=mi_vivienda, estado__nombre='Cerrada')
    elif proyectos_user is not None:
        cerradas_qs = Observacion.objects.filter(vivienda__proyecto__in=proyectos_user, estado__nombre='Cerrada')
        # if estado_id:
        #     cerradas_qs = cerradas_qs.filter(estado_id=estado_id)
        if fecha_inicio:
            cerradas_qs = cerradas_qs.filter(fecha_creacion__date__gte=fecha_inicio)
        if fecha_fin:
            cerradas_qs = cerradas_qs.filter(fecha_creacion__date__lte=fecha_fin)
    else:
        cerradas_qs = Observacion.objects.none()

    cerradas_por_mes = (
        cerradas_qs
        .annotate(mes=TruncMonth('fecha_cierre'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )
    meses_cerrados = [d['mes'].strftime('%b %Y') if d['mes'] else 'Sin fecha' for d in cerradas_por_mes]
    valores_cerrados = [d['total'] for d in cerradas_por_mes]

    context = {
        'total_proyectos': total_proyectos,
        'viviendas_total': viviendas_total,
        'viviendas_entregadas': viviendas_entregadas,
        'obs_total': obs_total,
        'obs_abiertas': obs_abiertas,
        'obs_cerradas': obs_cerradas,
        'obs_vencidas': obs_vencidas,
        'obs_urgentes': obs_urgentes,
        'porc_cerradas': porc_cerradas,
        'porc_abiertas': porc_abiertas,
        'porc_vencidas': porc_vencidas,
        'ultimas_observaciones': ultimas_observaciones,
        'viviendas_asignadas': viviendas_asignadas,
        'es_familia': es_familia,
        'is_admin': is_admin,
        'mi_vivienda': mi_vivienda,
        'sin_vivienda': sin_vivienda,
        'timestamp': int(datetime.now().timestamp()),
        'labels': labels,
        'values': values,
        'meses_cerrados': meses_cerrados,
        'valores_cerrados': valores_cerrados,
        'metrics_region': metrics_region,
        'comunas_valparaiso': comuna_objs,
        'cumplimiento_constructoras': cumplimiento_constructoras,
        'regiones': regiones,
    # 'estados': estados,  # Eliminado del contexto
    }

    return render(request, 'dashboard/index.html', context)

def ajax_comunas_por_region(request):
    region_id = request.GET.get('region_id')
    comunas = Comuna.objects.filter(region_id=region_id).values('id', 'nombre')
    return JsonResponse({'comunas': list(comunas)})
    
import logging

logger = logging.getLogger(__name__)

# ...existing code...

@login_required
@rol_requerido('ADMINISTRADOR', 'TECHO')
def maestro(request):
    # Determinar si el usuario es familia
    es_familia = (
        request.user.groups.filter(name='FAMILIA').exists() or 
        (hasattr(request.user, 'rol') and request.user.rol and request.user.rol.nombre == 'FAMILIA')
    )
    
    context = {
        'titulo': 'Panel Maestro',
        'es_familia': es_familia,
    }
    return render(request, 'maestro/index.html', context)

# Mixin para soft delete
class SoftDeleteMixin:
    def soft_delete(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        obj.activo = False
        obj.save()
        messages.success(request, f"{self.model._meta.verbose_name} desactivado.")
        return redirect(self.list_url_name)

# CRUD para Region
class RegionList(LoginRequiredMixin, RolRequiredMixin, SoftDeleteMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    model = Region
    list_url_name = 'maestro_region_list'

    def get(self, request):
        regions = Region.objects.filter(activo=True)
        return render(request, 'maestro/region_list.html', {'regions': regions, 'titulo': 'Regiones'})

class RegionCreate(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    def get(self, request):
        from .forms import RegionForm
        return render(request, 'maestro/region_form.html', {'form': RegionForm(), 'titulo': 'Crear Región'})

    def post(self, request):
        from .forms import RegionForm
        form = RegionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Región creada exitosamente.')
            return redirect('maestro_region_list')
        return render(request, 'maestro/region_form.html', {'form': form, 'titulo': 'Crear Región'})

class RegionUpdate(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    def get(self, request, pk):
        from .forms import RegionForm
        region = get_object_or_404(Region, pk=pk)
        return render(request, 'maestro/region_form.html', {'form': RegionForm(instance=region), 'titulo': 'Editar Región'})

    def post(self, request, pk):
        from .forms import RegionForm
        region = get_object_or_404(Region, pk=pk)
        form = RegionForm(request.POST, instance=region)
        if form.is_valid():
            form.save()
            messages.success(request, 'Región actualizada exitosamente.')
            return redirect('maestro_region_list')
        return render(request, 'maestro/region_form.html', {'form': form, 'titulo': 'Editar Región'})

class RegionDelete(LoginRequiredMixin, RolRequiredMixin, SoftDeleteMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    model = Region
    list_url_name = 'maestro_region_list'

    def post(self, request, pk):
        return self.soft_delete(request, pk)

# CRUD para Comuna
class ComunaList(LoginRequiredMixin, RolRequiredMixin, SoftDeleteMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    model = Comuna
    list_url_name = 'maestro_comuna_list'

    def get(self, request):
        comunas = Comuna.objects.filter(activo=True).select_related('region')
        return render(request, 'maestro/comuna_list.html', {'comunas': comunas, 'titulo': 'Comunas'})

class ComunaCreate(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    def get(self, request):
        from .forms import ComunaForm
        return render(request, 'maestro/comuna_form.html', {'form': ComunaForm(), 'titulo': 'Crear Comuna'})

    def post(self, request):
        from .forms import ComunaForm
        form = ComunaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Comuna creada exitosamente.')
            return redirect('maestro_comuna_list')
        return render(request, 'maestro/comuna_form.html', {'form': form, 'titulo': 'Crear Comuna'})

class ComunaUpdate(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    def get(self, request, pk):
        from .forms import ComunaForm
        comuna = get_object_or_404(Comuna, pk=pk)
        return render(request, 'maestro/comuna_form.html', {'form': ComunaForm(instance=comuna), 'titulo': 'Editar Comuna'})

    def post(self, request, pk):
        from .forms import ComunaForm
        comuna = get_object_or_404(Comuna, pk=pk)
        form = ComunaForm(request.POST, instance=comuna)
        if form.is_valid():
            form.save()
            messages.success(request, 'Comuna actualizada exitosamente.')
            return redirect('maestro_comuna_list')
        return render(request, 'maestro/comuna_form.html', {'form': form, 'titulo': 'Editar Comuna'})

class ComunaDelete(LoginRequiredMixin, RolRequiredMixin, SoftDeleteMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    model = Comuna
    list_url_name = 'maestro_comuna_list'

    def post(self, request, pk):
        return self.soft_delete(request, pk)

# CRUD para Rol
class RolList(LoginRequiredMixin, RolRequiredMixin, SoftDeleteMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    model = Rol
    list_url_name = 'maestro_rol_list'

    def get(self, request):
        # Mostrar todos los roles, activos e inactivos
        roles = Rol.objects.all()
        return render(request, 'maestro/rol_list.html', {'roles': roles, 'titulo': 'Roles'})

class RolCreate(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    def get(self, request):
        from .forms import RolForm
        return render(request, 'maestro/rol_form.html', {'form': RolForm(), 'titulo': 'Crear Rol'})

    def post(self, request):
        from .forms import RolForm
        form = RolForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rol creado exitosamente.')
            return redirect('maestro_rol_list')
        return render(request, 'maestro/rol_form.html', {'form': form, 'titulo': 'Crear Rol'})

class RolUpdate(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    def get(self, request, pk):
        from .forms import RolForm
        rol = get_object_or_404(Rol, pk=pk)
        return render(request, 'maestro/rol_form.html', {'form': RolForm(instance=rol), 'titulo': 'Editar Rol'})

    def post(self, request, pk):
        from .forms import RolForm
        rol = get_object_or_404(Rol, pk=pk)
        form = RolForm(request.POST, instance=rol)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rol actualizado exitosamente.')
            return redirect('maestro_rol_list')
        return render(request, 'maestro/rol_form.html', {'form': form, 'titulo': 'Editar Rol'})

class RolDelete(LoginRequiredMixin, RolRequiredMixin, SoftDeleteMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    model = Rol
    list_url_name = 'maestro_rol_list'

    def post(self, request, pk):
        return self.soft_delete(request, pk)
        
class RolActivate(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    """Reactivar un rol previamente desactivado"""
    def post(self, request, pk):
        # Buscar el rol y marcarlo como activo
        rol = get_object_or_404(Rol, pk=pk)
        rol.activo = True
        rol.save()
        messages.success(request, 'Rol activado exitosamente.')
        return redirect('maestro_rol_list')

# CRUD para Constructora
class ConstructoraList(LoginRequiredMixin, RolRequiredMixin, SoftDeleteMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    model = Constructora
    list_url_name = 'maestro_constructora_list'

    def get(self, request):
        rut = request.GET.get('rut', '').strip()
        constructoras = Constructora.objects.filter(activo=True).select_related('region', 'comuna')
        if rut:
            from django.db.models import Q
            constructoras = constructoras.filter(
                Q(rut__icontains=rut) | Q(nombre__icontains=rut)
            )
        return render(request, 'maestro/constructora_list.html', {
            'constructoras': constructoras,
            'titulo': 'Constructoras',
            'request': request
        })

class ConstructoraCreate(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    def get(self, request):
        from .forms import ConstructoraForm
        return render(request, 'maestro/constructora_form.html', {'form': ConstructoraForm(), 'titulo': 'Crear Constructora'})

    def post(self, request):
        from .forms import ConstructoraForm
        form = ConstructoraForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Constructora creada exitosamente.')
            return redirect('maestro_constructora_list')
        return render(request, 'maestro/constructora_form.html', {'form': form, 'titulo': 'Crear Constructora'})

class ConstructoraUpdate(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    def get(self, request, pk):
        from .forms import ConstructoraForm
        constructora = get_object_or_404(Constructora, pk=pk)
        return render(request, 'maestro/constructora_form.html', {'form': ConstructoraForm(instance=constructora), 'titulo': 'Editar Constructora'})

    def post(self, request, pk):
        from .forms import ConstructoraForm
        constructora = get_object_or_404(Constructora, pk=pk)
        form = ConstructoraForm(request.POST, instance=constructora)
        if form.is_valid():
            form.save()
            messages.success(request, 'Constructora actualizada exitosamente.')
            return redirect('maestro_constructora_list')
        return render(request, 'maestro/constructora_form.html', {'form': form, 'titulo': 'Editar Constructora'})

class ConstructoraDelete(LoginRequiredMixin, RolRequiredMixin, SoftDeleteMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    model = Constructora
    list_url_name = 'maestro_constructora_list'

    def post(self, request, pk):
        return self.soft_delete(request, pk)

# CRUD para Beneficiario
class BeneficiarioList(LoginRequiredMixin, RolRequiredMixin, SoftDeleteMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    model = Beneficiario
    list_url_name = 'maestro_beneficiario_list'

    def get(self, request):
        rut = request.GET.get('rut', '').strip()
        beneficiarios = Beneficiario.objects.filter(activo=True)
        if rut:
            beneficiarios = beneficiarios.filter(rut__icontains=rut)
        return render(request, 'maestro/beneficiario_list.html', {
            'beneficiarios': beneficiarios,
            'titulo': 'Beneficiarios',
            'request': request
        })

class BeneficiarioCreate(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    def get(self, request):
        from proyectos.forms import BeneficiarioForm
        return render(request, 'maestro/beneficiario_form.html', {'form': BeneficiarioForm(), 'titulo': 'Crear Beneficiario'})

    def post(self, request):
        from proyectos.forms import BeneficiarioForm
        form = BeneficiarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Beneficiario creado exitosamente.')
            return redirect('maestro_beneficiario_list')
        return render(request, 'maestro/beneficiario_form.html', {'form': form, 'titulo': 'Crear Beneficiario'})

class BeneficiarioUpdate(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    def get(self, request, pk):
        from proyectos.forms import BeneficiarioForm
        beneficiario = get_object_or_404(Beneficiario, pk=pk)
        return render(request, 'maestro/beneficiario_form.html', {'form': BeneficiarioForm(instance=beneficiario), 'titulo': 'Editar Beneficiario'})

    def post(self, request, pk):
        from proyectos.forms import BeneficiarioForm
        beneficiario = get_object_or_404(Beneficiario, pk=pk)
        form = BeneficiarioForm(request.POST, instance=beneficiario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Beneficiario actualizado exitosamente.')
            return redirect('maestro_beneficiario_list')
        return render(request, 'maestro/beneficiario_form.html', {'form': form, 'titulo': 'Editar Beneficiario'})

class BeneficiarioDelete(LoginRequiredMixin, RolRequiredMixin, SoftDeleteMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    model = Beneficiario
    list_url_name = 'maestro_beneficiario_list'

    def post(self, request, pk):
        return self.soft_delete(request, pk)

# CRUD para Usuario
class UsuarioList(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    def get(self, request):
        from .models import Rol
        rut = request.GET.get('rut', '').strip()
        correo = request.GET.get('correo', '').strip()
        rol = request.GET.get('rol', '').strip()
        empresa = request.GET.get('empresa', '').strip()
        usuarios = Usuario.objects.filter(is_active=True)
        if rut:
            usuarios = usuarios.filter(rut__icontains=rut)
        if correo:
            usuarios = usuarios.filter(email__icontains=correo)
        if rol:
            usuarios = usuarios.filter(rol__nombre=rol)
        if empresa:
            usuarios = usuarios.filter(empresa__icontains=empresa)
        
        # Obtener roles disponibles para el dropdown
        roles_disponibles = Rol.objects.filter(activo=True).order_by('nombre')
        
        return render(request, 'maestro/usuario_list.html', {
            'usuarios': usuarios,
            'titulo': 'Usuarios',
            'request': request,
            'roles_disponibles': roles_disponibles
        })

class UsuarioCreate(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    def get(self, request):
        from .forms import UsuarioForm
        return render(request, 'maestro/usuario_form.html', {'form': UsuarioForm(), 'titulo': 'Crear Usuario'})

    def post(self, request):
        from .forms import UsuarioForm
        form = UsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario creado exitosamente.')
            return redirect('maestro_usuario_list')
        return render(request, 'maestro/usuario_form.html', {'form': form, 'titulo': 'Crear Usuario'})

class UsuarioUpdate(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    def get(self, request, pk):
        from .forms import UsuarioForm
        usuario = get_object_or_404(Usuario, pk=pk)
        return render(request, 'maestro/usuario_form.html', {'form': UsuarioForm(instance=usuario), 'titulo': 'Editar Usuario'})

    def post(self, request, pk):
        from .forms import UsuarioForm
        usuario = get_object_or_404(Usuario, pk=pk)
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado exitosamente.')
            return redirect('maestro_usuario_list')
        return render(request, 'maestro/usuario_form.html', {'form': form, 'titulo': 'Editar Usuario'})

class UsuarioDelete(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    def post(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)
        usuario.is_active = False
        usuario.save()
        messages.success(request, 'Usuario desactivado.')
        return redirect('maestro_usuario_list')

# CRUD para Proyecto
class ProyectoList(LoginRequiredMixin, RolRequiredMixin, SoftDeleteMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    model = Proyecto
    list_url_name = 'maestro_proyecto_list'

    def get(self, request):
        search = request.GET.get('search', '').strip()
        estado = request.GET.get('estado', '').strip()
        proyectos = Proyecto.objects.filter(activo=True).select_related('region', 'comuna', 'creado_por')
        
        if search:
            proyectos = proyectos.filter(
                Q(codigo__icontains=search) |
                Q(nombre__icontains=search) |
                Q(constructora__nombre__icontains=search) |
                Q(region__nombre__icontains=search) |
                Q(comuna__nombre__icontains=search)
            )
        
        if estado:
            from datetime import datetime, timedelta
            hoy = datetime.now().date()
            dentro_30 = hoy + timedelta(days=30)
            if estado == 'vigente':
                proyectos = proyectos.filter(fecha_termino_postventa__gt=dentro_30)
            elif estado == 'por_vencer':
                proyectos = proyectos.filter(fecha_termino_postventa__gt=hoy, fecha_termino_postventa__lte=dentro_30)
            elif estado == 'vencido':
                proyectos = proyectos.filter(fecha_termino_postventa__lte=hoy)
            elif estado == 'sin_definir':
                proyectos = proyectos.filter(fecha_termino_postventa__isnull=True)
        
        return render(request, 'maestro/proyecto_list.html', {'proyectos': proyectos, 'titulo': 'Proyectos'})

class ProyectoCreate(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    def get(self, request):
        from proyectos.forms import ProyectoForm
        return render(request, 'maestro/proyecto_form.html', {'form': ProyectoForm(), 'titulo': 'Crear Proyecto'})

    def post(self, request):
        from proyectos.forms import ProyectoForm
        form = ProyectoForm(request.POST)
        if form.is_valid():
            proyecto = form.save(commit=False)
            proyecto.creado_por = request.user
            if form.cleaned_data.get('constructora'):
                proyecto.constructora = form.cleaned_data['constructora'].nombre
            proyecto.save()
            messages.success(request, f'Proyecto {proyecto.codigo} creado exitosamente.')
            return redirect('maestro_proyecto_list')
        return render(request, 'maestro/proyecto_form.html', {'form': form, 'titulo': 'Crear Proyecto'})

class ProyectoUpdate(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    def get(self, request, pk):
        from proyectos.forms import ProyectoForm
        proyecto = get_object_or_404(Proyecto, pk=pk)
        return render(request, 'maestro/proyecto_form.html', {'form': ProyectoForm(instance=proyecto), 'titulo': 'Editar Proyecto'})

    def post(self, request, pk):
        from proyectos.forms import ProyectoForm
        proyecto = get_object_or_404(Proyecto, pk=pk)
        form = ProyectoForm(request.POST, instance=proyecto)
        if form.is_valid():
            form.save()
            messages.success(request, f'Proyecto {proyecto.codigo} actualizado exitosamente.')
            return redirect('maestro_proyecto_list')
        return render(request, 'maestro/proyecto_form.html', {'form': form, 'titulo': 'Editar Proyecto'})

class ProyectoDelete(LoginRequiredMixin, RolRequiredMixin, SoftDeleteMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    model = Proyecto
    list_url_name = 'maestro_proyecto_list'

    def post(self, request, pk):
        return self.soft_delete(request, pk)

# CRUD para Vivienda
class ViviendaList(LoginRequiredMixin, RolRequiredMixin, SoftDeleteMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    model = Vivienda
    list_url_name = 'maestro_vivienda_list'

    def get(self, request):
        beneficiario = request.GET.get('beneficiario', '').strip()
        codigo = request.GET.get('codigo', '').strip()
        viviendas = Vivienda.objects.filter(activa=True).select_related('proyecto', 'tipologia', 'beneficiario')
        if beneficiario:
            # Normalizar rut buscado (eliminar puntos y guion)
            import re
            rut_normalizado = re.sub(r'[^\dKk]', '', beneficiario)
            from django.db import models
            viviendas = viviendas.annotate(
                rut_normalizado=models.Func(
                    models.F('beneficiario__rut'),
                    function='REPLACE',
                    template="REPLACE(REPLACE(REPLACE(%(expressions)s, '.', ''), '-', ''), ' ', '')"
                )
            ).filter(
                Q(rut_normalizado__icontains=rut_normalizado) |
                Q(beneficiario__nombre__icontains=beneficiario)
            )
        if codigo:
            viviendas = viviendas.filter(codigo__icontains=codigo)
        return render(request, 'maestro/vivienda_list.html', {'viviendas': viviendas, 'titulo': 'Viviendas'})

class ViviendaCreate(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    def get(self, request):
        from .forms import ViviendaForm
        return render(request, 'maestro/vivienda_form.html', {'form': ViviendaForm(), 'titulo': 'Crear Vivienda'})

    def post(self, request):
        from .forms import ViviendaForm
        form = ViviendaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vivienda creada exitosamente.')
            return redirect('maestro_vivienda_list')
        return render(request, 'maestro/vivienda_form.html', {'form': form, 'titulo': 'Crear Vivienda'})

class ViviendaUpdate(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    def get(self, request, pk):
        from .forms import ViviendaForm
        vivienda = get_object_or_404(Vivienda, pk=pk)
        return render(request, 'maestro/vivienda_form.html', {'form': ViviendaForm(instance=vivienda), 'titulo': 'Editar Vivienda'})

    def post(self, request, pk):
        from .forms import ViviendaForm
        vivienda = get_object_or_404(Vivienda, pk=pk)
        form = ViviendaForm(request.POST, instance=vivienda)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vivienda actualizada exitosamente.')
            return redirect('maestro_vivienda_list')
        return render(request, 'maestro/vivienda_form.html', {'form': form, 'titulo': 'Editar Vivienda'})

class ViviendaDelete(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    def post(self, request, pk):
        vivienda = get_object_or_404(Vivienda, pk=pk)
        vivienda.activa = False
        vivienda.save()
        messages.success(request, 'Vivienda desactivada.')
        return redirect('maestro_vivienda_list')

# CRUD para Observacion
class ObservacionList(LoginRequiredMixin, RolRequiredMixin, SoftDeleteMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    model = Observacion
    list_url_name = 'maestro_observacion_list'

    def get(self, request):
        from django.core.paginator import Paginator
        from django.db.models import Q, Count
        from incidencias.models import EstadoObservacion
        
        # Obtener parámetros de búsqueda
        buscar_rut = request.GET.get('rut', '').strip()
        buscar_vivienda = request.GET.get('vivienda', '').strip()
        filtro_estado = request.GET.get('estado', '')
        filtro_prioridad = request.GET.get('prioridad', '')
        buscar_texto = request.GET.get('buscar', '').strip()
        
        # Query base con relaciones necesarias
        observaciones_list = Observacion.objects.filter(activo=True).select_related(
            'proyecto', 'vivienda', 'vivienda__beneficiario', 'tipo', 'estado', 'creado_por'
        ).prefetch_related('archivos_adjuntos').annotate(
            total_archivos=Count('archivos_adjuntos')
        )
        
        # Aplicar filtros
        if buscar_rut:
            # Permitir búsqueda por RUT con o sin formato (puntos/guion)
            import re
            from django.db import models
            rut_normalizado = re.sub(r'[^\dKk]', '', buscar_rut)
            observaciones_list = observaciones_list.annotate(
                rut_normalizado=models.Func(
                    models.F('vivienda__beneficiario__rut'),
                    function='REPLACE',
                    template="REPLACE(REPLACE(REPLACE(%(expressions)s, '.', ''), '-', ''), ' ', '')"
                )
            ).filter(
                Q(rut_normalizado__icontains=rut_normalizado) |
                Q(vivienda__beneficiario__nombre__icontains=buscar_rut)
            )
        
        if buscar_vivienda:
            observaciones_list = observaciones_list.filter(
                Q(vivienda__codigo__icontains=buscar_vivienda) |
                Q(proyecto__codigo__icontains=buscar_vivienda) |
                Q(proyecto__nombre__icontains=buscar_vivienda)
            )
        
        if filtro_estado:
            observaciones_list = observaciones_list.filter(estado=filtro_estado)
        
        if filtro_prioridad:
            observaciones_list = observaciones_list.filter(prioridad=filtro_prioridad)
        
        if buscar_texto:
            observaciones_list = observaciones_list.filter(
                Q(elemento__icontains=buscar_texto) |
                Q(detalle__icontains=buscar_texto) |
                Q(creado_por__email__icontains=buscar_texto)
            )
        
        observaciones_list = observaciones_list.order_by('-fecha_creacion')
        
        # Paginación - 15 observaciones por página
        paginator = Paginator(observaciones_list, 15)
        page_number = request.GET.get('page')
        observaciones = paginator.get_page(page_number)
        
        # Datos para los filtros
        estados = EstadoObservacion.objects.filter(activo=True)
        prioridades = [
            ('baja', 'Baja'),
            ('normal', 'Normal'),
            ('alta', 'Alta'),
            ('urgente', 'Urgente'),
        ]
        
        context = {
            'observaciones': observaciones,
            'titulo': 'Observaciones',
            'estados': estados,
            'prioridades': prioridades,
            'filtros': {
                'rut': buscar_rut,
                'vivienda': buscar_vivienda,
                'estado': filtro_estado,
                'prioridad': filtro_prioridad,
                'buscar': buscar_texto,
            }
        }
        return render(request, 'maestro/observacion_list.html', context)

class ObservacionCreate(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    
    def get(self, request):
        from .forms import ObservacionForm
        form = ObservacionForm()
        return render(request, 'maestro/observacion_form.html', {
            'form': form, 
            'titulo': 'Crear Observación'
        })

    def post(self, request):
        from .forms import ObservacionForm
        form = ObservacionForm(request.POST, request.FILES)
        if form.is_valid():
            observacion = form.save(commit=False)
            observacion.creado_por = request.user
            
            # Sincronizar es_urgente con prioridad
            if observacion.es_urgente:
                observacion.prioridad = 'urgente'
            elif observacion.prioridad == 'urgente':
                observacion.es_urgente = True
            
            observacion.save()
            
            # Procesar archivos adjuntos
            archivos_adjuntos = request.FILES.getlist('archivos_adjuntos')
            archivos_guardados = 0
            
            if archivos_adjuntos:
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
            
            mensaje = 'Observación creada exitosamente.'
            if archivos_guardados > 0:
                mensaje += f' Se adjuntaron {archivos_guardados} archivo(s).'
            messages.success(request, mensaje)
            return redirect('maestro_observacion_list')
        
        return render(request, 'maestro/observacion_form.html', {
            'form': form, 
            'titulo': 'Crear Observación'
        })

class ObservacionUpdate(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    def get(self, request, pk):
        from .forms import ObservacionForm
        observacion = get_object_or_404(Observacion, pk=pk)
        return render(request, 'maestro/observacion_form.html', {'form': ObservacionForm(instance=observacion), 'titulo': 'Editar Observación'})

    def post(self, request, pk):
        from .forms import ObservacionForm
        observacion = get_object_or_404(Observacion, pk=pk)
        form = ObservacionForm(request.POST, request.FILES, instance=observacion)
        if form.is_valid():
            observacion = form.save(commit=False)
            
            # Sincronizar es_urgente con prioridad
            if observacion.es_urgente:
                observacion.prioridad = 'urgente'
            elif observacion.prioridad == 'urgente':
                observacion.es_urgente = True
            
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
            
            mensaje = 'Observación actualizada exitosamente.'
            if archivos_guardados > 0:
                mensaje += f' Se adjuntaron {archivos_guardados} archivo(s) adicional(es).'
            messages.success(request, mensaje)
            return redirect('maestro_observacion_list')
        return render(request, 'maestro/observacion_form.html', {'form': form, 'titulo': 'Editar Observación'})

class ObservacionDelete(LoginRequiredMixin, RolRequiredMixin, SoftDeleteMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    model = Observacion
    list_url_name = 'maestro_observacion_list'

    def post(self, request, pk):
        return self.soft_delete(request, pk)


# CRUD para Configuración de Observaciones
class ConfiguracionObservacionView(LoginRequiredMixin, RolRequiredMixin, View):
    roles_permitidos = ['ADMINISTRADOR', 'TECHO']
    """Vista para ver y editar la configuración de observaciones"""
    
    def get(self, request):
        from .models import ConfiguracionObservacion
        from .forms import ConfiguracionObservacionForm
        
        config = ConfiguracionObservacion.get_configuracion()
        form = ConfiguracionObservacionForm(instance=config)
        
        context = {
            'form': form,
            'config': config,
            'titulo': 'Configuración de Observaciones'
        }
        return render(request, 'maestro/configuracion_observacion.html', context)
    
    def post(self, request):
        from .models import ConfiguracionObservacion
        from .forms import ConfiguracionObservacionForm
        
        config = ConfiguracionObservacion.get_configuracion()
        form = ConfiguracionObservacionForm(request.POST, instance=config)
        
        if form.is_valid():
            config = form.save(commit=False)
            config.modificado_por = request.user
            config.save()
            messages.success(request, 'Configuración actualizada exitosamente.')
            return redirect('maestro_configuracion_observacion')
        
        context = {
            'form': form,
            'config': config,
            'titulo': 'Configuración de Observaciones'
        }
        return render(request, 'maestro/configuracion_observacion.html', context)

@login_required
def buscar_beneficiario_por_rut(request):
    """Vista AJAX para buscar un beneficiario por RUT"""
    from proyectos.models import Beneficiario
    from django.db.models import Q
    
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        rut_original = request.GET.get('rut', '').strip()
        
        if not rut_original:
            return JsonResponse({
                'success': False,
                'error': 'RUT requerido'
            })
        
        # Limpiar RUT para la búsqueda: remover puntos, espacios y guiones
        def normalizar_rut(rut):
            return rut.replace('.', '').replace(' ', '').replace('-', '').lower()

        rut_normalizado = normalizar_rut(rut_original)

        try:
            # Buscar todos los beneficiarios activos
            beneficiarios = Beneficiario.objects.filter(activo=True)
            beneficiario = None
            for b in beneficiarios:
                if b.rut:
                    if normalizar_rut(b.rut) == rut_normalizado:
                        beneficiario = b
                        break

            if beneficiario:
                return JsonResponse({
                    'success': True,
                    'beneficiario': {
                        'id': beneficiario.id,
                        'nombre_completo': beneficiario.nombre_completo,
                        'rut': beneficiario.rut,
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'No se encontró un beneficiario activo con RUT {rut_original}'
                })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al buscar beneficiario: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Solicitud inválida'
    })
