from django.core.management.base import BaseCommand
from incidencias.models import Observacion
from django.utils import timezone
import random
from datetime import timedelta, datetime
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Asigna fechas aleatorias de creación y cierre a observaciones cerradas en 2025.'

    def handle(self, *args, **options):
        obs_cerradas = Observacion.objects.filter(estado__nombre='Cerrada')
        count = 0
        for obs in obs_cerradas:
            # Fecha de creación aleatoria en 2025
            fecha_inicio = datetime(2025, 1, 1, 8, 0, 0)
            fecha_fin = datetime(2025, 12, 31, 18, 0, 0)
            delta = fecha_fin - fecha_inicio
            random_days = random.randint(0, delta.days)
            random_seconds = random.randint(0, 10*60*60)  # entre 8:00 y 18:00
            fecha_creacion = fecha_inicio + timedelta(days=random_days, seconds=random_seconds)

            # Si es urgente, cierre máximo 48h después; si no, hasta 120 días
            if obs.es_urgente:
                max_cierre = fecha_creacion + timedelta(hours=48)
            else:
                max_cierre = fecha_creacion + timedelta(days=120)
            # No pasar de 2025-12-31
            fecha_cierre_max = min(max_cierre, datetime(2025, 12, 31, 23, 59, 59))
            cierre_delta = fecha_cierre_max - fecha_creacion
            cierre_segundos = random.randint(1, int(cierre_delta.total_seconds()))
            fecha_cierre = fecha_creacion + timedelta(seconds=cierre_segundos)
            # Asegurar que fecha_vencimiento no viole la constraint respecto a fecha_creacion
            if obs.fecha_vencimiento:
                try:
                    # Si la fecha_vencimiento es anterior a la fecha de creación nueva, ajustarla al mismo día de creación
                    if obs.fecha_vencimiento < fecha_creacion.date():
                        obs.fecha_vencimiento = fecha_creacion.date()
                except Exception:
                    # En caso inesperado, dejar fecha_vencimiento como estaba
                    pass

            obs.fecha_creacion = fecha_creacion
            obs.fecha_cierre = fecha_cierre
            try:
                obs.save(update_fields=['fecha_creacion', 'fecha_cierre', 'fecha_vencimiento'])
            except IntegrityError as e:
                # Mostrar un mensaje y continuar con la siguiente observación
                self.stdout.write(self.style.WARNING(f"Omitida observación id={obs.pk} por IntegrityError: {e}"))
                continue
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Actualizadas {count} observaciones cerradas con fechas aleatorias en 2025.'))
