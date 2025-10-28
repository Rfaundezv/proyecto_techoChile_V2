
from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from core.models import Region

class Command(BaseCommand):
    help = 'Lista todas las regiones con viviendas, mostrando total de viviendas, proyectos y comunas con viviendas.'

    def handle(self, *args, **options):
        self.stdout.write('=== Reporte de Viviendas por Región ===')
        from core.utils.region_metrics import get_region_metrics
        metrics = get_region_metrics()
        for region in metrics:
            if region['total_viviendas'] > 0:
                self.stdout.write(f"\n--- {region['region']} ---")
                self.stdout.write(f"Total viviendas: {region['total_viviendas']}")
                self.stdout.write(f"Entregadas: {region['entregadas']}")
                self.stdout.write(f"Observaciones: {region['casos_postventa']}")
                self.stdout.write(f"Tiempo promedio de solución: {region['promedio_dias']} días" if region['promedio_dias'] != '-' else "Tiempo promedio de solución: -")
