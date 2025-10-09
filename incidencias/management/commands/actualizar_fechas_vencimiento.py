from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from incidencias.models import Observacion
from core.models import ConfiguracionObservacion


class Command(BaseCommand):
    help = 'Actualiza las fechas de vencimiento de observaciones que no tienen fecha asignada'

    def handle(self, *args, **options):
        config = ConfiguracionObservacion.get_configuracion()
        
        # Buscar observaciones sin fecha de vencimiento
        observaciones_sin_fecha = Observacion.objects.filter(
            fecha_vencimiento__isnull=True,
            activo=True
        )
        
        contador = 0
        for obs in observaciones_sin_fecha:
            if obs.es_urgente:
                # Urgente: 48 horas = 2 días desde la creación
                dias_urgente = (config.horas_vencimiento_urgente + 23) // 24
                obs.fecha_vencimiento = obs.fecha_creacion.date() + timedelta(days=dias_urgente)
            else:
                # Normal: 120 días desde la creación
                obs.fecha_vencimiento = obs.fecha_creacion.date() + timedelta(days=config.dias_vencimiento_normal)
            
            obs.save()
            contador += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Observación #{obs.pk} - {"URGENTE" if obs.es_urgente else "NORMAL"} - '
                    f'Vencimiento: {obs.fecha_vencimiento}'
                )
            )
        
        if contador == 0:
            self.stdout.write(self.style.WARNING('No se encontraron observaciones sin fecha de vencimiento'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Total actualizado: {contador} observación(es)')
            )
