from django.db.models import Count, Q, Avg, F, ExpressionWrapper, DurationField
from core.models import Region
from proyectos.models import Proyecto, Vivienda
from incidencias.models import Observacion

def get_region_metrics(region_id=None, estado_id=None, fecha_inicio=None, fecha_fin=None):
    regiones_qs = Region.objects.filter(activo=True)
    if region_id:
        regiones_qs = regiones_qs.filter(id=region_id)
    regiones = regiones_qs.order_by('nombre')
    metrics = []
    for region in regiones:
        # Solo proyectos activos de la región actual
        proyectos_objs = Proyecto.objects.filter(region=region, activo=True)
        if estado_id:
            proyectos_objs = proyectos_objs.filter(estado_id=estado_id)
        if fecha_inicio:
            proyectos_objs = proyectos_objs.filter(fecha_creacion__date__gte=fecha_inicio)
        if fecha_fin:
            proyectos_objs = proyectos_objs.filter(fecha_creacion__date__lte=fecha_fin)
        viviendas_qs = Vivienda.objects.filter(proyecto__in=proyectos_objs, activa=True)
        viviendas_ids = viviendas_qs.values_list('id', flat=True)
        total_viviendas = viviendas_qs.count()
        entregadas = viviendas_qs.filter(estado='entregada').count()
        if total_viviendas == 0:
            continue
        obs_region = Observacion.objects.filter(vivienda_id__in=viviendas_ids, activo=True)
        if estado_id:
            obs_region = obs_region.filter(estado_id=estado_id)
        if fecha_inicio:
            obs_region = obs_region.filter(fecha_creacion__date__gte=fecha_inicio)
        if fecha_fin:
            obs_region = obs_region.filter(fecha_creacion__date__lte=fecha_fin)
        total_obs = obs_region.count()
        obs_cerradas = obs_region.filter(estado__nombre='Cerrada', fecha_cierre__isnull=False, fecha_creacion__isnull=False)
        tiempo_promedio = None
        if obs_cerradas.exists():
            expr = ExpressionWrapper(F('fecha_cierre') - F('fecha_creacion'), output_field=DurationField())
            promedio = obs_cerradas.annotate(duracion=expr).aggregate(prom=Avg('duracion'))['prom']
            if promedio is not None:
                tiempo_promedio = int(promedio.total_seconds() // 86400)
        metrics.append({
            'region': region.nombre,
            'total_viviendas': total_viviendas,
            'entregadas': entregadas,
            'casos_postventa': total_obs,
            'promedio_dias': tiempo_promedio if tiempo_promedio is not None else '-',
        })
    return metrics
