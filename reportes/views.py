from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import transaction
from datetime import datetime
import os
from django.conf import settings
from io import BytesIO

# Indicador de disponibilidad de WeasyPrint (se comprueba solo cuando se necesita)
WEASYPRINT_AVAILABLE = False  # reservado para uso futuro si queremos memoizar la comprobación

# Fallback a ReportLab
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    # Definir valores por defecto si no está disponible
    inch = 72
    cm = 28.35

# Usaremos WeasyPrint si está instalado; de lo contrario, caemos a ReportLab

from .models import ActaRecepcion, FamiliarBeneficiario  # , ConstructorActa
from proyectos.models import Vivienda, Proyecto, Beneficiario
from core.decorators import rol_requerido


@login_required
def index(request):
    """Vista principal de reportes"""
    context = {
        'titulo': 'Reportes y Documentos',
        'total_actas': ActaRecepcion.objects.count(),
        'actas_mes': ActaRecepcion.objects.filter(
            fecha_creacion__month=timezone.now().month,
            fecha_creacion__year=timezone.now().year
        ).count(),
    }
    return render(request, 'reportes/index.html', context)


@login_required
@rol_requerido('ADMINISTRADOR', 'TECHO')
def acta_list(request):
    """Lista de actas de recepción"""
    actas = ActaRecepcion.objects.select_related(
        'vivienda', 'proyecto', 'beneficiario'
    ).order_by('-fecha_creacion')
    
    # Filtros
    proyecto_id = request.GET.get('proyecto')
    if proyecto_id:
        actas = actas.filter(proyecto_id=proyecto_id)
    
    context = {
        'titulo': 'Actas de Recepción',
        'actas': actas,
        'proyectos': Proyecto.objects.filter(activo=True).order_by('nombre'),
    }
    return render(request, 'reportes/acta_list.html', context)


@login_required
@rol_requerido('ADMINISTRADOR', 'TECHO')
def acta_create(request):
    """Crear nueva acta de recepción"""
    from .forms import ActaRecepcionForm
    
    if request.method == 'POST':
        form = ActaRecepcionForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    acta = form.save(commit=False)
                    acta.save()
                    
                    messages.success(request, f'Acta {acta.numero_acta} creada exitosamente.')
                    return redirect('reportes:acta_detail', pk=acta.pk)
            except Exception as e:
                messages.error(request, f'Error al crear el acta: {str(e)}')
        else:
            # Mostrar errores específicos del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, f'Error: {error}')
                    else:
                        messages.error(request, f'Error en {field}: {error}')
    else:
        form = ActaRecepcionForm()
    
    context = {
        'titulo': 'Crear Acta de Recepción',
        'form': form,
        'proyectos': Proyecto.objects.filter(activo=True).order_by('nombre'),
    }
    return render(request, 'reportes/acta_create.html', context)


@login_required
def acta_detail(request, pk):
    """Ver detalle de acta"""
    acta = get_object_or_404(
        ActaRecepcion.objects.select_related(
            'vivienda', 'proyecto', 'beneficiario'
        ).prefetch_related('familiares'),  # 'constructor_info'
        pk=pk
    )
    
    context = {
        'titulo': f'Acta {acta.numero_acta}',
        'acta': acta,
    }
    return render(request, 'reportes/acta_detail.html', context)


@login_required  
def acta_pdf(request, pk):
    """Generar PDF del acta - con opción de descarga"""
    acta = get_object_or_404(
        ActaRecepcion.objects.select_related(
            'vivienda', 'proyecto', 'beneficiario'  
        ).prefetch_related('familiares'),
        pk=pk
    )
    
    es_descarga = request.GET.get('download') == '1'
    
    # GENERAR PDF completo si download=1
    if es_descarga:
        # Ruta mínima de diagnóstico: generar un PDF básico si ?mode=min
        if request.GET.get('mode') == 'min':
            try:
                from reportlab.pdfgen import canvas  # type: ignore
                buffer = BytesIO()
                c = canvas.Canvas(buffer, pagesize=A4)
                c.drawString(100, 800, f"Acta {acta.numero_acta} - PDF minimal")
                c.drawString(100, 780, timezone.now().strftime('%d/%m/%Y %H:%M'))
                c.showPage()
                c.save()
                buffer.seek(0)
                response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="Acta_{acta.numero_acta}_minimal.pdf"'
                response['X-PDF-Engine'] = 'reportlab-min'
                return response
            except Exception as e:
                print(f"ERROR PDF minimal: {e}")
        # 1) Intentar con WeasyPrint primero para replicar el HTML/CSS
        try:
            import weasyprint  # type: ignore
            context = {
                'acta': acta,
                'proyecto': acta.proyecto,
                'beneficiario': acta.beneficiario,
                'vivienda': acta.vivienda,
                'familiares': acta.familiares.all(),
                'fecha_generacion': timezone.now(),
                'es_descarga': True,
                'para_pdf': True,
            }
            html_content = render_to_string('reportes/acta_template.html', context, request=request)
            pdf_file = weasyprint.HTML(string=html_content, base_url=request.build_absolute_uri('/')).write_pdf()
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="Acta de Recepción - {acta.numero_acta}.pdf"'
            response['X-PDF-Engine'] = 'weasyprint'
            return response
        except Exception:
            import traceback
            print("ERROR PDF WeasyPrint:\n" + traceback.format_exc())
        # 2) Intentar con ReportLab (estable en Windows)
        # Usar ReportLab si está disponible a nivel de módulo

        if REPORTLAB_AVAILABLE:
            try:
                # Generar PDF usando ReportLab
                buffer = BytesIO()
                doc = SimpleDocTemplate(
                    buffer,
                    pagesize=A4,
                    rightMargin=2*cm,
                    leftMargin=2*cm,
                    topMargin=2*cm,
                    bottomMargin=2*cm,
                )

                # Estilos personalizados que coincidan con el HTML
                styles = getSampleStyleSheet()

                # Estilo para el encabezado principal
                header_style = ParagraphStyle(
                    'CustomHeader',
                    parent=styles['Title'],
                    fontSize=18,
                    spaceAfter=10,
                    alignment=1,  # Centrado
                    textColor=colors.black,
                    fontName='Helvetica-Bold'
                )

                # Estilo para subtítulo
                subtitle_style = ParagraphStyle(
                    'CustomSubtitle',
                    parent=styles['Heading2'],
                    fontSize=14,
                    spaceAfter=20,
                    alignment=1,
                    textColor=colors.black,
                    fontName='Helvetica-Bold'
                )

                # Estilo para secciones
                section_style = ParagraphStyle(
                    'SectionHeader',
                    parent=styles['Heading3'],
                    fontSize=12,
                    spaceBefore=15,
                    spaceAfter=10,
                    textColor=colors.black,
                    fontName='Helvetica-Bold'
                )

                # Estilo para texto normal
                normal_style = ParagraphStyle(
                    'CustomNormal',
                    parent=styles['Normal'],
                    fontSize=10,
                    spaceAfter=4,
                    fontName='Helvetica'
                )

                story = []

                # === ENCABEZADO ===
                story.append(Paragraph("ACTA DE RECEPCIÓN DE VIVIENDA", header_style))
                story.append(Paragraph("TECHO CHILE", subtitle_style))
                story.append(Paragraph(f"<b>Acta N°:</b> {acta.numero_acta} | <b>Generada:</b> {timezone.now().strftime('%d/%m/%Y %H:%M')}", normal_style))
                story.append(Spacer(1, 20))

                # === INFORMACIÓN DEL PROYECTO ===
                story.append(Paragraph("INFORMACIÓN DEL PROYECTO", section_style))
                proyecto_data = [
                    ['Proyecto:', acta.proyecto.nombre if acta.proyecto else 'N/A'],
                    ['Comuna:', acta.proyecto.comuna.nombre if (acta.proyecto and acta.proyecto.comuna) else 'N/A'],
                    ['Región:', acta.proyecto.region.nombre if (acta.proyecto and acta.proyecto.region) else 'N/A'],
                ]

                for label, value in proyecto_data:
                    story.append(Paragraph(f"<b>{label}</b> {value}", normal_style))
                story.append(Spacer(1, 12))

                # === INFORMACIÓN DEL BENEFICIARIO ===
                story.append(Paragraph("INFORMACIÓN DEL BENEFICIARIO", section_style))
                if acta.beneficiario:
                    # Construir string de teléfonos activos
                    telefonos_activos = list(acta.beneficiario.telefonos.filter(activo=True).values_list('numero', flat=True))
                    if not telefonos_activos:
                        telefonos_activos = list(acta.beneficiario.telefonos.values_list('numero', flat=True)[:1])
                    telefonos_str = ', '.join(telefonos_activos) if telefonos_activos else 'N/A'

                    beneficiario_data = [
                        ['Nombre Completo:', f"{acta.beneficiario.nombre} {acta.beneficiario.apellido_paterno} {acta.beneficiario.apellido_materno or ''}".strip()],
                        ['RUT:', acta.beneficiario.rut or 'N/A'],
                        ['Teléfonos:', telefonos_str],
                        ['Email:', acta.beneficiario.email or 'N/A'],
                    ]

                    for label, value in beneficiario_data:
                        story.append(Paragraph(f"<b>{label}</b> {value}", normal_style))
                else:
                    story.append(Paragraph("<b>Beneficiario:</b> No asignado", normal_style))
                story.append(Spacer(1, 12))

                # === INFORMACIÓN DE LA VIVIENDA ===
                story.append(Paragraph("INFORMACIÓN DE LA VIVIENDA", section_style))
                if acta.vivienda:
                    vivienda_data = [
                        ['Código de Vivienda:', acta.vivienda.codigo],
                        ['Tipología:', acta.vivienda.tipologia.nombre if acta.vivienda.tipologia else 'N/A'],
                        ['Estado:', acta.vivienda.get_estado_display()],
                        ['Familia Beneficiaria:', acta.vivienda.familia_beneficiaria or 'N/A'],
                    ]

                    for label, value in vivienda_data:
                        story.append(Paragraph(f"<b>{label}</b> {value}", normal_style))
                else:
                    story.append(Paragraph("<b>Vivienda:</b> No asignada", normal_style))
                story.append(Spacer(1, 12))

                # === DETALLES DEL ACTA ===
                story.append(Paragraph("DETALLES DEL ACTA", section_style))
                acta_data = [
                    ['Fecha de Entrega:', acta.fecha_entrega.strftime("%d/%m/%Y") if acta.fecha_entrega else 'N/A'],
                    ['Entrega Conforme:', 'Sí' if acta.entregado_beneficiario else 'No'],
                    ['Estructura:', 'Conforme' if getattr(acta, 'estado_estructura', True) else 'Con observaciones'],
                    ['Instalaciones:', 'Conforme' if getattr(acta, 'estado_instalaciones', True) else 'Con observaciones'],
                ]

                for label, value in acta_data:
                    story.append(Paragraph(f"<b>{label}</b> {value}", normal_style))
                story.append(Spacer(1, 15))

                # === FAMILIARES (si los hay) ===
                familiares = acta.familiares.all()
                if familiares.exists():
                    story.append(Paragraph("FAMILIARES REGISTRADOS", section_style))

                    # Crear tabla de familiares
                    familiares_data = [['Nombre Completo', 'Parentesco', 'RUT', 'Edad']]
                    for familiar in familiares:
                        familiares_data.append([
                            familiar.nombre_completo,
                            familiar.parentesco,
                            familiar.rut or 'N/A',
                            str(familiar.edad) if familiar.edad else 'N/A'
                        ])

                    familiares_table = Table(familiares_data, colWidths=[8*cm, 3*cm, 3*cm, 2*cm])
                    familiares_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))

                    story.append(familiares_table)
                    story.append(Spacer(1, 15))

                # === OBSERVACIONES ===
                if acta.observaciones:
                    story.append(Paragraph("OBSERVACIONES", section_style))
                    story.append(Paragraph(acta.observaciones, normal_style))
                    story.append(Spacer(1, 20))

                # === FIRMAS ===
                story.append(Spacer(1, 30))
                story.append(Paragraph("FIRMAS Y CONFORMIDAD", section_style))

                # Tabla de firmas
                firma_data = [
                    ['', '', ''],
                    ['_________________________', '_________________________', '_________________________'],
                    ['Beneficiario', 'Representante TECHO', 'Supervisor'],
                    ['', '', ''],
                    ['Fecha: _______________', 'Fecha: _______________', 'Fecha: _______________']
                ]

                firma_table = Table(firma_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
                firma_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
                    ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ]))

                story.append(firma_table)

                # Construir PDF
                doc.build(story)

                # Preparar respuesta PDF
                buffer.seek(0)
                response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="Acta de Recepción - {acta.numero_acta}.pdf"'
                response['X-PDF-Engine'] = 'reportlab'

                return response

            except Exception as e:
                # Log del error pero continuar con HTML
                import traceback
                print("ERROR PDF ReportLab:\n" + traceback.format_exc())

        # (WeasyPrint ya fue intentado arriba)

        # 3) Si ambos fallaron, generar un PDF mínimo como último recurso
        try:
            from reportlab.pdfgen import canvas  # type: ignore
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            c.setFont('Helvetica', 12)
            c.drawString(72, 800, f"Acta {acta.numero_acta}")
            c.drawString(72, 780, "No se pudo generar el PDF completo. Este es un PDF mínimo de respaldo.")
            c.drawString(72, 760, timezone.now().strftime('%d/%m/%Y %H:%M'))
            c.showPage()
            c.save()
            buffer.seek(0)
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="Acta de Recepción - {acta.numero_acta} (respaldo).pdf"'
            response['X-PDF-Engine'] = 'reportlab-min-fallback'
            return response
        except Exception:
            return HttpResponse("No se pudo generar el PDF en este momento.", status=500, content_type='text/plain; charset=utf-8')
    
    # HTML por defecto (vista previa)
    context = {
        'acta': acta,
        'proyecto': acta.proyecto,
        'beneficiario': acta.beneficiario,
        'vivienda': acta.vivienda,
        'familiares': acta.familiares.all(),
        'fecha_generacion': timezone.now(),
        'es_descarga': es_descarga,
    }
    
    html_content = render_to_string('reportes/acta_template.html', context)
    
    if es_descarga:
        # Si no logramos generar PDF, mostramos HTML sin forzar descarga binaria
        response = HttpResponse(html_content, content_type='text/html')
        response['Content-Disposition'] = f'inline; filename="Acta_{acta.numero_acta}_{timezone.now().strftime("%Y%m%d")}.html"'
        response['X-PDF-Engine'] = 'html-fallback'
    else:
        response = HttpResponse(html_content, content_type='text/html')
        response['X-PDF-Engine'] = 'html-view'
    
    return response


@login_required
def get_viviendas_by_proyecto(request):
    """AJAX: Obtener viviendas por proyecto"""
    proyecto_id = request.GET.get('proyecto_id')
    viviendas = Vivienda.objects.filter(
        proyecto_id=proyecto_id,
        activa=True,
        beneficiario__isnull=False
    ).select_related('beneficiario').values(
        'id', 'codigo', 'beneficiario__nombre_completo'
    )
    
    return JsonResponse(list(viviendas), safe=False)


@login_required
def get_vivienda_data(request):
    """AJAX: Obtener datos de la vivienda para prellenar el formulario"""
    vivienda_id = request.GET.get('vivienda_id')
    vivienda = get_object_or_404(
        Vivienda.objects.select_related(
            'beneficiario', 'proyecto', 'proyecto__constructora', 'tipologia'
        ), 
        id=vivienda_id
    )
    
    # Obtener teléfono del beneficiario
    telefono = ""
    if vivienda.beneficiario and vivienda.beneficiario.telefonos.exists():
        telefono = vivienda.beneficiario.telefonos.filter(activo=True).first().numero
    
    # Mapear tipo estructura desde tipología si existe
    tipos_validos = {'madera', 'metalica', 'mixta', 'hormigon'}
    tipo_estructura_tipologia = getattr(vivienda.tipologia, 'tipo_estructura', None) if vivienda.tipologia else None
    tipo_estructura_res = tipo_estructura_tipologia if (isinstance(tipo_estructura_tipologia, str) and tipo_estructura_tipologia.lower() in tipos_validos) else None

    data = {
        'beneficiario': {
            'nombre_completo': vivienda.beneficiario.nombre_completo if vivienda.beneficiario else '',
            'rut': vivienda.beneficiario.rut if vivienda.beneficiario else '',
            'email': vivienda.beneficiario.email if vivienda.beneficiario else '',
            'telefono': telefono,
        },
        'proyecto': {
            'nombre': vivienda.proyecto.nombre,
            'comuna': vivienda.proyecto.comuna.nombre,
            'region': vivienda.proyecto.region.nombre,
        },
        'constructora': {
            'nombre': vivienda.proyecto.constructora.nombre,
            'rut': vivienda.proyecto.constructora.rut or '',
            'telefono': vivienda.proyecto.constructora.telefono or '',
        } if vivienda.proyecto.constructora else None,
        'vivienda': {
            'codigo': vivienda.codigo,
            'direccion': f"{vivienda.proyecto.nombre} - Vivienda {vivienda.codigo}",
            'superficie': getattr(vivienda.tipologia, 'metros_cuadrados', None),
            'ambientes': getattr(vivienda.tipologia, 'numero_ambientes', None),
            'tipo_estructura': tipo_estructura_res,
        }
    }
    
    return JsonResponse(data)


@login_required
@rol_requerido('ADMINISTRADOR', 'TECHO')
def acta_edit(request, pk):
    """Editar acta de recepción"""
    from .forms import ActaRecepcionForm
    
    acta = get_object_or_404(ActaRecepcion, pk=pk)
    
    if request.method == 'POST':
        form = ActaRecepcionForm(request.POST, instance=acta)
        if form.is_valid():
            try:
                acta = form.save()
                messages.success(request, f'Acta {acta.numero_acta} actualizada exitosamente.')
                return redirect('reportes:acta_detail', pk=acta.pk)
            except Exception as e:
                messages.error(request, f'Error al actualizar el acta: {str(e)}')
        else:
            # Mostrar errores específicos del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, f'Error: {error}')
                    else:
                        messages.error(request, f'Error en {field}: {error}')
    else:
        form = ActaRecepcionForm(instance=acta)
    
    context = {
        'titulo': f'Editar Acta {acta.numero_acta}',
        'form': form,
        'acta': acta,
        'proyectos': Proyecto.objects.filter(activo=True).order_by('nombre'),
    }
    return render(request, 'reportes/acta_edit.html', context)


@login_required
@rol_requerido('ADMINISTRADOR', 'TECHO')
def acta_delete(request, pk):
    """Eliminar acta de recepción"""
    acta = get_object_or_404(ActaRecepcion, pk=pk)
    
    if request.method == 'POST':
        try:
            numero_acta = acta.numero_acta
            acta.delete()
            messages.success(request, f'Acta {numero_acta} eliminada exitosamente.')
            return redirect('reportes:acta_list')
        except Exception as e:
            messages.error(request, f'Error al eliminar el acta: {str(e)}')
            return redirect('reportes:acta_detail', pk=pk)
    
    # Si no es POST, redirigir al detalle
    return redirect('reportes:acta_detail', pk=pk)


@login_required
def buscar_beneficiario_ajax(request):
    """Vista AJAX para buscar datos del beneficiario por RUT"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Solicitud no válida'})
    
    rut = request.GET.get('rut', '').strip()
    if not rut:
        return JsonResponse({'success': False, 'error': 'RUT requerido'})
    
    try:
        # Buscar beneficiario por RUT
        beneficiario = Beneficiario.objects.select_related().get(rut=rut, activo=True)
        
        # Obtener datos de la vivienda asociada
        vivienda = None
        proyecto = None
        observaciones_previas = ""
        
        try:
            vivienda = beneficiario.vivienda
            if vivienda:
                proyecto = vivienda.proyecto
                observaciones_previas = vivienda.observaciones_generales or ""
        except:
            pass
        
        # Obtener observaciones de incidencias si existen
        try:
            from incidencias.models import Observacion
            observaciones_incidencias = Observacion.objects.filter(
                vivienda=vivienda,
                activo=True
            ).select_related('estado').values_list('descripcion', 'estado__nombre', 'es_urgente')
            
            if observaciones_incidencias:
                obs_lines = []
                obs_lines.append("OBSERVACIONES DE LA VIVIENDA:")
                obs_lines.append("=" * 40)
                
                for desc, estado, es_urgente in observaciones_incidencias:
                    plazo = "48 HORAS" if es_urgente else "120 DÍAS"
                    obs_lines.append(f"• {desc}")
                    obs_lines.append(f"  Estado: {estado} | Plazo: {plazo}")
                    obs_lines.append("")
                
                obs_texto = "\n".join(obs_lines)
                
                if observaciones_previas:
                    observaciones_previas = f"{observaciones_previas}\n\n{obs_texto}"
                else:
                    observaciones_previas = obs_texto
        except Exception as e:
            # Si hay error con incidencias, al menos incluir observaciones generales
            print(f"Error obteniendo observaciones: {e}")
            if not observaciones_previas and vivienda:
                observaciones_previas = vivienda.observaciones_generales or ""
        
        # Preparar datos de respuesta
        # Mapear tipo de estructura de tipología al choice del Acta (fallback 'madera')
        tipo_estructura_tipologia = None
        if vivienda and vivienda.tipologia:
            tipo_estructura_tipologia = getattr(vivienda.tipologia, 'tipo_estructura', None)
        tipos_validos = {'madera', 'metalica', 'mixta', 'hormigon'}
        tipo_estructura_res = tipo_estructura_tipologia if (isinstance(tipo_estructura_tipologia, str) and tipo_estructura_tipologia.lower() in tipos_validos) else 'madera'

        data = {
            'success': True,
            'beneficiario': {
                'id': beneficiario.id,
                'nombre_completo': beneficiario.nombre_completo,
                'rut': beneficiario.rut,
                'email': beneficiario.email or '',
                'proyecto_id': proyecto.id if proyecto else None,
                'proyecto_nombre': str(proyecto) if proyecto else '',
                'vivienda_id': vivienda.id if vivienda else None,
                'vivienda_codigo': vivienda.codigo if vivienda else '',
                'observaciones': observaciones_previas,
                'direccion_proyecto': f"{proyecto.nombre}, {proyecto.comuna.nombre}" if proyecto else '',
                'vivienda': {
                    # Nombres de claves esperadas por el front
                    'superficie': getattr(vivienda.tipologia, 'metros_cuadrados', None) or 18,
                    'tipo_estructura': tipo_estructura_res,
                    'ambientes': getattr(vivienda.tipologia, 'numero_ambientes', None) or 2,
                    'codigo': vivienda.codigo if vivienda else '',
                    'tipologia': vivienda.tipologia.nombre if vivienda and vivienda.tipologia else 'Vivienda Básica',
                } if vivienda else {
                    'superficie': 18,
                    'ambientes': 2,
                    'tipo_estructura': 'madera'
                }
            }
        }
        
        return JsonResponse(data)
        
    except Beneficiario.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': f'No se encontró beneficiario con RUT {rut}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'Error al buscar beneficiario: {str(e)}'
        })