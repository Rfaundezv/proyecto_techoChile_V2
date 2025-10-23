from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from proyectos.models import Proyecto, Vivienda, Beneficiario
from incidencias.models import Observacion
from django.db.models import Func, F

@login_required
def reporte_observaciones_filtradas(request):
    proyectos = Proyecto.objects.filter(activo=True)
    viviendas = Vivienda.objects.filter(activa=True)
    beneficiarios = Beneficiario.objects.filter(activo=True)
    observaciones = None
    filtro_aplicado = False

    proyecto_id = request.GET.get('proyecto')
    vivienda_id = request.GET.get('vivienda')
    rut = request.GET.get('rut', '').strip()

    if proyecto_id or vivienda_id or rut:
        filtro_aplicado = True
        obs_query = Observacion.objects.select_related('vivienda', 'vivienda__proyecto', 'vivienda__beneficiario', 'estado')
        if proyecto_id:
            obs_query = obs_query.filter(vivienda__proyecto_id=proyecto_id)
        if vivienda_id:
            obs_query = obs_query.filter(vivienda_id=vivienda_id)
        if rut:
            rut_normalizado = rut.replace('.', '').replace('-', '')
            obs_query = obs_query.annotate(
                rut_normalizado=Func(F('vivienda__beneficiario__rut'), function='REPLACE', template="REPLACE(REPLACE(%(expressions)s, '.', ''), '-', '')")
            ).filter(rut_normalizado=rut_normalizado)
        observaciones = obs_query.all()
    
    context = {
        'proyectos': proyectos,
        'viviendas': viviendas,
        'beneficiarios': beneficiarios,
        'observaciones': observaciones,
        'filtro_aplicado': filtro_aplicado,
    }
    return render(request, 'reportes/filtrar_observaciones.html', context)

@login_required
def reporte_observaciones_filtradas_excel(request):
    import openpyxl
    from django.http import HttpResponse
    proyecto_id = request.GET.get('proyecto')
    vivienda_id = request.GET.get('vivienda')
    rut = request.GET.get('rut', '').strip()
    obs_query = Observacion.objects.select_related('vivienda', 'vivienda__proyecto', 'vivienda__beneficiario', 'estado').prefetch_related('seguimientos')
    if proyecto_id:
        obs_query = obs_query.filter(vivienda__proyecto_id=proyecto_id)
    if vivienda_id:
        obs_query = obs_query.filter(vivienda_id=vivienda_id)
    if rut:
        rut_normalizado = rut.replace('.', '').replace('-', '')
        obs_query = obs_query.annotate(
            rut_normalizado=Func(F('vivienda__beneficiario__rut'), function='REPLACE', template="REPLACE(REPLACE(%(expressions)s, '.', ''), '-', '')")
        ).filter(rut_normalizado=rut_normalizado)
    observaciones = obs_query.all()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Observaciones Filtradas"
    headers = [
        "ID", "Proyecto", "Vivienda", "Beneficiario", "RUT", "Estado", "Detalle", "Notas Seguimiento", "Fecha Creación", "Urgente",
        "Historial - Fecha", "Historial - Acción", "Historial - Comentario", "Historial - Estado Anterior", "Historial - Estado Nuevo"
    ]
    ws.append(headers)
    for o in observaciones:
        # Datos principales de la observación
        base_row = [
            o.id,
            o.vivienda.proyecto.nombre if o.vivienda and o.vivienda.proyecto else "",
            o.vivienda.codigo if o.vivienda else "",
            o.vivienda.beneficiario.nombre_completo if o.vivienda and o.vivienda.beneficiario else "",
            o.vivienda.beneficiario.rut if o.vivienda and o.vivienda.beneficiario else "",
            o.estado.nombre if o.estado else "",
            o.detalle,
            o.observaciones_seguimiento if o.observaciones_seguimiento else "",
            o.fecha_creacion.strftime('%d/%m/%Y') if o.fecha_creacion else "",
            "Sí" if o.es_urgente else "No"
        ]
        seguimientos = list(o.seguimientos.all())
        if seguimientos:
            for s in seguimientos:
                ws.append(base_row + [
                    s.fecha.strftime('%d/%m/%Y %H:%M'),
                    s.accion,
                    s.comentario if s.comentario else "",
                    getattr(s.estado_anterior, 'nombre', ''),
                    getattr(s.estado_nuevo, 'nombre', '')
                ])
        else:
            # Si no hay seguimientos, dejar columnas de historial vacías
            ws.append(base_row + ["", "", "", "", ""])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=observaciones_filtradas.xlsx'
    wb.save(response)
    return response
