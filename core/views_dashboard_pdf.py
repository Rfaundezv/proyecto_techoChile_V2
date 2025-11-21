
from django.shortcuts import render

def generando_reporte(request):
    """Vista que muestra la pantalla de espera mientras se genera el PDF."""
    return render(request, 'dashboard/generando_reporte.html')

def dashboard_pdf_report(request):
    from django.db.models import Count, Q
    # Importar utilidades dentro de la función para evitar errores de importación
    from core.utils.region_metrics import get_region_metrics
    from core.utils.cumplimiento_constructora import get_cumplimiento_plazos_por_constructora

    # Reutilizar la lógica del dashboard
    region_id = request.GET.get('region')
    estado_id = request.GET.get('estado')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    metrics_region = get_region_metrics(region_id=region_id, estado=estado_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
    cumplimiento_constructoras = get_cumplimiento_plazos_por_constructora(region_id=region_id, estado=estado_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

    # --- Datos para portada ---
    from proyectos.models import Proyecto, Vivienda
    from incidencias.models import Observacion
    from core.models import Region
    from datetime import datetime
    # Obtener nombre de usuario compatible con modelo personalizado
    user = request.user
    if hasattr(user, 'first_name') and hasattr(user, 'last_name'):
        nombre = f"{user.first_name} {user.last_name}".strip()
        usuario_reporte = nombre if nombre else (getattr(user, 'username', None) or getattr(user, 'email', 'Usuario'))
    else:
        usuario_reporte = getattr(user, 'username', None) or getattr(user, 'email', 'Usuario')
    periodo_reporte = request.GET.get('periodo', '') or datetime.now().strftime('%B %Y')
    region_nombre = Region.objects.get(id=region_id).nombre if region_id else 'Todas'

    # Filtrar por región si corresponde
    proyectos_qs = Proyecto.objects.filter(activo=True)
    viviendas_qs = Vivienda.objects.filter(activa=True)
    obs_qs = Observacion.objects.filter(activo=True)
    if region_id:
        proyectos_qs = proyectos_qs.filter(region_id=region_id)
        viviendas_qs = viviendas_qs.filter(proyecto__region_id=region_id)
        obs_qs = obs_qs.filter(vivienda__proyecto__region_id=region_id)
    if fecha_inicio:
        proyectos_qs = proyectos_qs.filter(fecha_creacion__date__gte=fecha_inicio)
        viviendas_qs = viviendas_qs.filter(proyecto__fecha_creacion__date__gte=fecha_inicio)
        obs_qs = obs_qs.filter(fecha_creacion__date__gte=fecha_inicio)
    if fecha_fin:
        proyectos_qs = proyectos_qs.filter(fecha_creacion__date__lte=fecha_fin)
        viviendas_qs = viviendas_qs.filter(proyecto__fecha_creacion__date__lte=fecha_fin)
        obs_qs = obs_qs.filter(fecha_creacion__date__lte=fecha_fin)

    proyectos_total = proyectos_qs.count()
    viviendas_total = viviendas_qs.count()
    obs_total = obs_qs.count()
    fecha_reporte = datetime.now().strftime('%d/%m/%Y %H:%M')


    # KPIs principales
    viviendas_entregadas = viviendas_qs.filter(estado='entregada').count()
    porc_viviendas_entregadas = round((viviendas_entregadas / viviendas_total) * 100, 1) if viviendas_total else 0
    casos_postventa_abiertos = obs_qs.filter(estado__nombre='Abierta').count()
    # Tiempo promedio de resolución (en días)
    from django.db.models import F, ExpressionWrapper, DurationField, Avg
    obs_cerradas = obs_qs.filter(estado__nombre='Cerrada', fecha_cierre__isnull=False, fecha_creacion__isnull=False)
    if obs_cerradas.exists():
        expr = ExpressionWrapper(F('fecha_cierre') - F('fecha_creacion'), output_field=DurationField())
        promedio = obs_cerradas.annotate(duracion=expr).aggregate(prom=Avg('duracion'))['prom']
        tiempo_promedio_resolucion = int(promedio.total_seconds() // 86400) if promedio else 0
    else:
        tiempo_promedio_resolucion = 0
    # Familias acompañadas: viviendas con beneficiario
    familias_acompañadas = viviendas_qs.exclude(beneficiario__isnull=True).count()
    porc_familias_acompañadas = round((familias_acompañadas / viviendas_total) * 100, 1) if viviendas_total else 0
    tasa_cumplimiento = cumplimiento_constructoras['global']
    kpi = {
        'total_viviendas': viviendas_total,
        'viviendas_entregadas': viviendas_entregadas,
        'porc_viviendas_entregadas': porc_viviendas_entregadas,
        'casos_postventa_abiertos': casos_postventa_abiertos,
        'tiempo_promedio_resolucion': tiempo_promedio_resolucion,
        'familias_acompañadas': familias_acompañadas,
        'porc_familias_acompañadas': porc_familias_acompañadas,
        'tasa_cumplimiento': tasa_cumplimiento,
    }

    # Estados de vivienda
    estados_vivienda = viviendas_qs.values('estado').annotate(cantidad=Count('id')).order_by('-cantidad')
    total_viv = viviendas_total
    tabla_estado_vivienda = []
    for ev in estados_vivienda:
        nombre = ev['estado'].capitalize() if ev['estado'] else 'Sin estado'
        cantidad = ev['cantidad']
        porcentaje = round((cantidad / total_viv) * 100, 1) if total_viv else 0
        tabla_estado_vivienda.append({'nombre': nombre, 'cantidad': cantidad, 'porcentaje': porcentaje})
    grafico_estado_vivienda = ''  # Puedes generar imagen si lo deseas

    # Diagnóstico técnico - Observaciones por tipo
    tipos_obs = obs_qs.values('tipo__nombre').annotate(
        totales=Count('id'),
        cerrados=Count('id', filter=Q(estado__nombre='Cerrada')),
        pendientes=Count('id', filter=Q(estado__nombre='Abierta')),
        tiempo_promedio=Avg(ExpressionWrapper(F('fecha_cierre') - F('fecha_creacion'), output_field=DurationField()), filter=Q(estado__nombre='Cerrada', fecha_cierre__isnull=False, fecha_creacion__isnull=False))
    ).order_by('-totales')
    tabla_observaciones = []
    for t in tipos_obs:
        if t['tiempo_promedio']:
            dias = int(t['tiempo_promedio'].total_seconds() // 86400)
        else:
            dias = '-'
        tabla_observaciones.append({
            'tipo': t['tipo__nombre'] or 'Sin tipo',
            'totales': t['totales'],
            'cerrados': t['cerrados'],
            'pendientes': t['pendientes'],
            'tiempo_promedio': f"{dias} días" if dias != '-' else '-',
        })
    grafico_observaciones_tipo = ''

    # Tendencias temporales (casos abiertos/cerrados por mes)
    from django.db.models.functions import TruncMonth
    obs_mes = obs_qs.annotate(mes=TruncMonth('fecha_creacion')).values('mes').annotate(
        abiertos=Count('id', filter=Q(estado__nombre='Abierta')),
        cerrados=Count('id', filter=Q(estado__nombre='Cerrada'))
    ).order_by('mes')
    tabla_tendencia_mensual = []
    prev_cerrados = 0
    for m in obs_mes:
        nombre = m['mes'].strftime('%B') if m['mes'] else 'Sin mes'
        abiertos = m['abiertos']
        cerrados = m['cerrados']
        variacion = cerrados - prev_cerrados
        tabla_tendencia_mensual.append({'nombre': nombre, 'abiertos': abiertos, 'cerrados': cerrados, 'variacion': f"{variacion:+d}"})
        prev_cerrados = cerrados
    grafico_tendencia_mensual = ''

    # Desempeño regional
    tabla_regional = []
    # Si hay filtro de región, solo mostrar esa región en la tabla regional
    for r in metrics_region:
        if not region_id or (region_id and str(r.get('region_id', '')) == str(region_id)):
            tabla_regional.append({
                'region': r['region'],
                'total': r['total_viviendas'],
                'entregadas': r['entregadas'],
                'casos': r['casos_postventa'],
                'tiempo': f"{r['promedio_dias']} días" if r['promedio_dias'] != '-' else '-',
                'satisfaccion': '-',  # Puedes calcular si tienes encuestas
                'estado': '-',        # Se puede calcular con reglas abajo
            })
    grafico_mapa_calor = ''

    # Desempeño del equipo (por técnico/coordinador)
    from django.contrib.auth import get_user_model
    User = get_user_model()
    tecnicos = User.objects.filter(is_active=True, rol__nombre__in=['TECNICO', 'COORDINADOR'])
    tabla_equipo = []
    for t in tecnicos:
        asignados = obs_qs.filter(asignado_a=t).count()
        cerrados = obs_qs.filter(asignado_a=t, estado__nombre='Cerrada').count()
        tasa_cierre = round((cerrados / asignados) * 100, 1) if asignados else 0
        tiempo_promedio = '-'
        obs_cerradas = obs_qs.filter(asignado_a=t, estado__nombre='Cerrada', fecha_cierre__isnull=False, fecha_creacion__isnull=False)
        if obs_cerradas.exists():
            expr = ExpressionWrapper(F('fecha_cierre') - F('fecha_creacion'), output_field=DurationField())
            promedio = obs_cerradas.annotate(duracion=expr).aggregate(prom=Avg('duracion'))['prom']
            if promedio:
                tiempo_promedio = f"{int(promedio.total_seconds() // 86400)} días"
        tabla_equipo.append({
            'nombre': t.get_full_name() if hasattr(t, 'get_full_name') else (t.first_name + ' ' + t.last_name).strip() or t.username,
            'asignados': asignados,
            'cerrados': cerrados,
            'tasa_cierre': f"{tasa_cierre}%",
            'tiempo_promedio': tiempo_promedio,
        })

    # Satisfacción (si tienes encuestas, aquí solo placeholder)
    satisfaccion_promedio = '-'
    encuestas_recibidas = '-'
    encuestas_esperadas = '-'
    motivos_insatisfaccion = '-'

    # --- Reglas automáticas para conclusiones, alertas, áreas de mejora, fortalezas y recomendaciones ---
    alertas = []
    areas_mejora = []
    fortalezas = []
    recomendaciones = []
    conclusiones = []

    # Alertas críticas
    if casos_postventa_abiertos > 50:
        alertas.append(f"Casos de postventa abiertos superan 50: {casos_postventa_abiertos}")
        recomendaciones.append("Reforzar gestión de cierre de casos y priorizar recursos en postventa.")
    if tiempo_promedio_resolucion > 15:
        alertas.append(f"Tiempo promedio de resolución excede 15 días: {tiempo_promedio_resolucion} días")
        recomendaciones.append("Implementar seguimiento semanal a casos abiertos y capacitación en resolución rápida.")
    if len(tabla_equipo) < 10:
        alertas.append(f"Menos de 10 técnicos activos: {len(tabla_equipo)}")
        recomendaciones.append("Revisar dotación y considerar contratación/refuerzo de técnicos.")
    for reg in tabla_regional:
        if reg['casos'] > 20:
            alertas.append(f"Región {reg['region']} supera 20 casos abiertos: {reg['casos']}")
            recomendaciones.append(f"Priorizar recursos y visitas en la región {reg['region']} para reducir backlog.")
    if tasa_cumplimiento < 80:
        alertas.append(f"Tasa de cumplimiento de plazos crítica: {tasa_cumplimiento}%")
        recomendaciones.append("Revisar procesos y causas de retraso en cierre de observaciones.")

    # Áreas de mejora
    for obs in tabla_observaciones:
        if obs['totales'] > 0 and obs['pendientes'] / obs['totales'] > 0.3:
            areas_mejora.append(f"Alto porcentaje de pendientes en {obs['tipo']}: {obs['pendientes']} de {obs['totales']}")
            recomendaciones.append(f"Revisar causas de demora en cierre de observaciones tipo {obs['tipo']}.")
    if tasa_cumplimiento < 90:
        areas_mejora.append(f"Tasa de cumplimiento de plazos baja: {tasa_cumplimiento}% (meta: 90%)")
        recomendaciones.append("Aumentar seguimiento y control de plazos en postventa.")
    if porc_viviendas_entregadas < 60:
        areas_mejora.append(f"Porcentaje de viviendas entregadas bajo lo esperado: {porc_viviendas_entregadas}%")
        recomendaciones.append("Acelerar procesos de entrega y resolver bloqueos administrativos.")
    if porc_familias_acompañadas < 70:
        areas_mejora.append(f"Porcentaje de familias acompañadas bajo lo esperado: {porc_familias_acompañadas}%")
        recomendaciones.append("Reforzar acompañamiento y seguimiento a familias beneficiarias.")

    # Fortalezas
    if porc_viviendas_entregadas > 70:
        fortalezas.append(f"Más del 70% de viviendas entregadas: {porc_viviendas_entregadas}%")
    for reg in tabla_regional:
        if reg['casos'] < 5:
            fortalezas.append(f"Región {reg['region']} con menos de 5 casos abiertos")
    if porc_familias_acompañadas > 80:
        fortalezas.append(f"Más del 80% de familias acompañadas: {porc_familias_acompañadas}%")
    if tasa_cumplimiento > 95:
        fortalezas.append(f"Tasa de cumplimiento de plazos sobresaliente: {tasa_cumplimiento}%")

    # Conclusiones ejecutivas
    if not alertas:
        conclusiones.append("El sistema de postventa se encuentra bajo control, sin alertas críticas.")
    else:
        conclusiones.append("Existen alertas críticas que requieren atención prioritaria del equipo ejecutivo.")
    if fortalezas:
        conclusiones.append("Se observan fortalezas importantes en la gestión y acompañamiento.")
    if areas_mejora:
        conclusiones.append("Se identifican áreas de mejora que deben ser abordadas para optimizar resultados.")

    # Proyecciones y metas (más detalladas)
    proyeccion_casos = max(0, casos_postventa_abiertos - int(0.1 * casos_postventa_abiertos))  # Proyección: reducción del 10%
    metas_trimestre = (
        f"Reducir casos abiertos a menos de 30, aumentar cumplimiento a 90%, "
        f"elevar porcentaje de viviendas entregadas sobre 75% y familias acompañadas sobre 85%."
    )
    recursos_estimados = f"Dotación mínima recomendada: {max(10, len(tabla_equipo))} técnicos, presupuesto adicional para capacitación y seguimiento."

    # Anexos técnicos (casos críticos y datos complementarios)
    anexos_casos_criticos = '\n'.join([
        f"Caso #{o.id}: {o.detalle[:40]}..." for o in obs_qs.filter(estado__nombre='Abierta').order_by('-fecha_creacion')[:10]
    ]) or 'Sin casos críticos destacados.'
    anexos_datos_complementarios = f"Total de observaciones: {obs_total}. Total de proyectos activos: {proyectos_total}. Total de viviendas activas: {viviendas_total}."
    anexos_metodologia = (
        'Indicadores calculados según reglas automáticas del sistema. '
        'Alertas y recomendaciones generadas en base a umbrales definidos por la dirección ejecutiva y mejores prácticas del sector.'
    )

    alertas_criticas = '\n'.join(alertas) if alertas else 'Sin alertas críticas.'
    areas_mejora_str = '\n'.join(areas_mejora) if areas_mejora else 'Sin áreas de mejora detectadas.'
    fortalezas_str = '\n'.join(fortalezas) if fortalezas else 'Sin fortalezas destacadas.'
    recomendaciones_list = recomendaciones if recomendaciones else ['Sin recomendaciones adicionales.']
    conclusiones_list = conclusiones if conclusiones else ['Sin conclusiones ejecutivas.']

    context = {
        'usuario_reporte': usuario_reporte,
        'periodo_reporte': periodo_reporte,
        'fecha_reporte': fecha_reporte,
        'region_nombre': region_nombre,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'kpi': kpi,
        'metrics_region': metrics_region,
        'cumplimiento_constructoras': cumplimiento_constructoras,
        'proyectos_total': proyectos_total,
        'viviendas_total': viviendas_total,
        'obs_total': obs_total,
        'tabla_estado_vivienda': tabla_estado_vivienda,
        'grafico_estado_vivienda': grafico_estado_vivienda,
        'tabla_observaciones': tabla_observaciones,
        'grafico_observaciones_tipo': grafico_observaciones_tipo,
        'tabla_tendencia_mensual': tabla_tendencia_mensual,
        'grafico_tendencia_mensual': grafico_tendencia_mensual,
        'tabla_regional': tabla_regional,
        'grafico_mapa_calor': grafico_mapa_calor,
        'tabla_equipo': tabla_equipo,
        'satisfaccion_promedio': satisfaccion_promedio,
        'encuestas_recibidas': encuestas_recibidas,
        'encuestas_esperadas': encuestas_esperadas,
        'motivos_insatisfaccion': motivos_insatisfaccion,
        'alertas_criticas': alertas_criticas,
        'areas_mejora': areas_mejora_str,
        'fortalezas': fortalezas_str,
        'proyeccion_casos': proyeccion_casos,
        'metas_trimestre': metas_trimestre,
        'recursos_estimados': recursos_estimados,
        'anexos_casos_criticos': anexos_casos_criticos,
        'anexos_datos_complementarios': anexos_datos_complementarios,
        'anexos_metodologia': anexos_metodologia,
        'recomendaciones': recomendaciones_list,
        'conclusiones': conclusiones_list,
    }

    from django.template.loader import render_to_string
    html_string = render_to_string('dashboard/reporte_pdf.html', context)
    if request.GET.get('preview') == '1':
        from django.http import HttpResponse
        return HttpResponse(html_string)

    # Usar xhtml2pdf en lugar de WeasyPrint para compatibilidad con Windows
    from django.http import HttpResponse
    from io import BytesIO
    from xhtml2pdf import pisa
    import os
    from datetime import datetime, timedelta
    from reportes.models import ReporteGenerado
    
    # Generar PDF con xhtml2pdf
    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(html_string, dest=pdf_buffer)
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF', status=500)
    pdf = pdf_buffer.getvalue()
    pdf_buffer.close()

    # Definir filtros relevantes para identificar duplicados
    filtros_dict = {
        'region': region_id,
        'estado': estado_id,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    usuario = request.user if request.user.is_authenticated else None

    # Buscar si ya existe un reporte igual en los últimos 10 minutos
    ahora = datetime.now()
    hace_10min = ahora - timedelta(minutes=10)
    reporte_existente = ReporteGenerado.objects.filter(
        usuario=usuario,
        filtros=filtros_dict,
        fecha_generacion__gte=hace_10min
    ).order_by('-fecha_generacion').first()

    if reporte_existente:
        # Usar el archivo ya generado
        ruta_absoluta = os.path.join(os.path.dirname(os.path.dirname(__file__)), reporte_existente.ruta_archivo)
        with open(ruta_absoluta, 'rb') as f:
            pdf = f.read()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{reporte_existente.nombre_archivo}"'
        return response

    # Si no existe, generar uno nuevo
    fecha_hora = ahora.strftime('%Y%m%d_%H%M')
    filename = f"reporte_techoChile_{fecha_hora}.pdf"
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'

    # Guardar PDF en carpeta local
    ruta_reporte = os.path.join('reportes_generados', filename)
    ruta_absoluta = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reportes_generados', filename)
    with open(ruta_absoluta, 'wb') as f:
        f.write(pdf)

    # Registrar metadatos en la base de datos
    try:
        ReporteGenerado.objects.create(
            usuario=usuario,
            nombre_archivo=filename,
            ruta_archivo=ruta_reporte,
            fecha_generacion=ahora,
            filtros=filtros_dict
        )
    except Exception as e:
        pass  # Si hay error, continuar igual

    return response
