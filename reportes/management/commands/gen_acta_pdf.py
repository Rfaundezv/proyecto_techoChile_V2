from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from reportes.models import ActaRecepcion

class Command(BaseCommand):
    help = 'Genera un PDF del acta (ReportLab) a un archivo para depurar'

    def add_arguments(self, parser):
        parser.add_argument('acta_id', type=int, help='ID del acta')
        parser.add_argument('--out', type=str, default='acta_debug.pdf', help='Ruta del archivo de salida')

    def handle(self, *args, **options):
        acta_id = options['acta_id']
        out = options['out']

        try:
            acta = ActaRecepcion.objects.select_related('proyecto', 'vivienda', 'beneficiario').prefetch_related('familiares').get(pk=acta_id)
        except ActaRecepcion.DoesNotExist:
            raise CommandError(f'Acta {acta_id} no existe')

        try:
            from io import BytesIO
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.lib.units import cm

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

            styles = getSampleStyleSheet()
            header_style = ParagraphStyle('Header', parent=styles['Title'], fontSize=18, alignment=1)
            section_style = ParagraphStyle('Section', parent=styles['Heading3'], fontSize=12)
            normal_style = ParagraphStyle('NormalX', parent=styles['Normal'], fontSize=10)

            story = []
            story.append(Paragraph('ACTA DE RECEPCIÓN DE VIVIENDA', header_style))
            story.append(Paragraph(f"Acta N°: {acta.numero_acta}", normal_style))
            story.append(Paragraph(f"Generada: {timezone.now().strftime('%d/%m/%Y %H:%M')}", normal_style))
            story.append(Spacer(1, 20))

            story.append(Paragraph('INFORMACIÓN DEL PROYECTO', section_style))
            story.append(Paragraph(f"Proyecto: {acta.proyecto.nombre}", normal_style))
            story.append(Paragraph(f"Comuna: {acta.proyecto.comuna.nombre}", normal_style))
            story.append(Paragraph(f"Región: {acta.proyecto.region.nombre}", normal_style))
            story.append(Spacer(1, 12))

            story.append(Paragraph('INFORMACIÓN DEL BENEFICIARIO', section_style))
            story.append(Paragraph(f"Nombre: {acta.beneficiario.nombre_completo}", normal_style))
            story.append(Paragraph(f"RUT: {acta.beneficiario.rut or 'N/A'}", normal_style))
            story.append(Paragraph(f"Email: {acta.beneficiario.email or 'N/A'}", normal_style))
            story.append(Spacer(1, 12))

            story.append(Paragraph('INFORMACIÓN DE LA VIVIENDA', section_style))
            story.append(Paragraph(f"Código: {acta.vivienda.codigo}", normal_style))
            story.append(Paragraph(f"Tipología: {getattr(acta.vivienda.tipologia, 'nombre', 'N/A')}", normal_style))
            story.append(Spacer(1, 12))

            doc.build(story)
            with open(out, 'wb') as f:
                f.write(buffer.getvalue())
            self.stdout.write(self.style.SUCCESS(f'PDF generado: {out}'))
        except Exception as e:
            raise CommandError(f'Error generando PDF: {e}')
