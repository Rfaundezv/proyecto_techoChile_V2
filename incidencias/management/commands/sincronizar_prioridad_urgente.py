from django.core.management.base import BaseCommand
from incidencias.models import Observacion

class Command(BaseCommand):
    help = 'Sincroniza el campo es_urgente con prioridad=urgente en todas las observaciones'

    def handle(self, *args, **options):
        # Sincronizar: si es_urgente=True entonces prioridad='urgente'
        actualizadas_urgente = Observacion.objects.filter(
            es_urgente=True
        ).exclude(
            prioridad='urgente'
        ).update(prioridad='urgente')
        
        # Sincronizar: si prioridad='urgente' entonces es_urgente=True
        actualizadas_flag = Observacion.objects.filter(
            prioridad='urgente'
        ).exclude(
            es_urgente=True
        ).update(es_urgente=True)
        
        total = actualizadas_urgente + actualizadas_flag
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Sincronizadas {total} observación(es)')
        )
        self.stdout.write(f'  - {actualizadas_urgente} con es_urgente=True → prioridad=urgente')
        self.stdout.write(f'  - {actualizadas_flag} con prioridad=urgente → es_urgente=True')
