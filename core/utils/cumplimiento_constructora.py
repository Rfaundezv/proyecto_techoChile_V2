from django.db.models import Count, Q, F
from core.models import Constructora
from proyectos.models import Proyecto, Vivienda
from incidencias.models import Observacion

def get_cumplimiento_plazos_por_constructora(region_id=None, estado_id=None, fecha_inicio=None, fecha_fin=None):
    """
    Retorna un diccionario con el porcentaje de cumplimiento de plazos por constructora:
    Cumplimiento = (observaciones cerradas antes de la fecha de vencimiento / total observaciones cerradas) * 100
    Permite filtrar por región, estado, fechas.
    """
    data = {}
    constructoras = Constructora.objects.filter(activo=True, proyecto__isnull=False).distinct()
    from django.utils import timezone
    today = timezone.now().date()
    for cons in constructoras:
        proyectos = Proyecto.objects.filter(constructora=cons)
        if region_id:
            proyectos = proyectos.filter(region_id=region_id)
        if estado_id:
            proyectos = proyectos.filter(estado_id=estado_id)
        if fecha_inicio:
            proyectos = proyectos.filter(fecha_creacion__date__gte=fecha_inicio)
        if fecha_fin:
            proyectos = proyectos.filter(fecha_creacion__date__lte=fecha_fin)
        viviendas = Vivienda.objects.filter(proyecto__in=proyectos)
        # Observaciones cerradas con fecha de cierre y vencimiento
        obs_cerradas = Observacion.objects.filter(
            vivienda__in=viviendas,
            estado__nombre='Cerrada',
            fecha_cierre__isnull=False,
            fecha_vencimiento__isnull=False
        )
        # Observaciones abiertas con fecha de vencimiento
        obs_abiertas = Observacion.objects.filter(
            vivienda__in=viviendas,
            estado__nombre='Abierta',
            fecha_vencimiento__isnull=False
        )
        if estado_id:
            obs_cerradas = obs_cerradas.filter(estado_id=estado_id)
            obs_abiertas = obs_abiertas.filter(estado_id=estado_id)
        if fecha_inicio:
            obs_cerradas = obs_cerradas.filter(fecha_creacion__date__gte=fecha_inicio)
            obs_abiertas = obs_abiertas.filter(fecha_creacion__date__gte=fecha_inicio)
        if fecha_fin:
            obs_cerradas = obs_cerradas.filter(fecha_creacion__date__lte=fecha_fin)
            obs_abiertas = obs_abiertas.filter(fecha_creacion__date__lte=fecha_fin)
        # Total: todas las observaciones con fecha de vencimiento (cerradas + abiertas)
        total = obs_cerradas.count() + obs_abiertas.count()
        # Cumplidas en plazo:
        # - Cerradas en plazo
        en_plazo_cerradas = obs_cerradas.filter(fecha_cierre__date__lte=F('fecha_vencimiento')).count()
        # - Abiertas que aún no vencen
        en_plazo_abiertas = obs_abiertas.filter(fecha_vencimiento__gt=today).count()
        en_plazo = en_plazo_cerradas + en_plazo_abiertas
        porcentaje = int((en_plazo / total) * 100) if total > 0 else 0
        data[cons.nombre] = porcentaje
    return data
