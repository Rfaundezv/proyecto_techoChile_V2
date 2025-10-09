from django.core.management.base import BaseCommand
from incidencias.models import TipoObservacion, EstadoObservacion

class Command(BaseCommand):
    help = 'Carga datos iniciales para el sistema de incidencias'

    def handle(self, *args, **kwargs):
        # Tipos de observación - TODOS con 'descripcion' sin tilde
        tipos = [
            {'nombre': 'General', 'descripcion': 'Observación general'},
            {'nombre': 'Estructural', 'descripcion': 'Problemas estructurales'},
            {'nombre': 'Instalaciones', 'descripcion': 'Instalaciones eléctricas, agua, gas'},
            {'nombre': 'Terminaciones', 'descripcion': 'Pintura, pisos, azulejos'},
            {'nombre': 'Carpintería', 'descripcion': 'Puertas, ventanas, muebles'},
            {'nombre': 'Sanitario', 'descripcion': 'Baños, grifería, sanitarios'},
        ]

        for tipo_data in tipos:
            tipo, created = TipoObservacion.objects.get_or_create(
                nombre=tipo_data['nombre'],
                defaults={'descripcion': tipo_data['descripcion']}
            )
            if created:
                self.stdout.write(f'Creado tipo: {tipo.nombre}')

        # Estados de observación
        estados = [
            {'codigo': 1, 'nombre': 'Abierta', 'descripcion': 'Observación registrada, pendiente de atención'},
            {'codigo': 2, 'nombre': 'En Proceso', 'descripcion': 'Observación en proceso de resolución'},
            {'codigo': 3, 'nombre': 'Cerrada', 'descripcion': 'Observación resuelta y cerrada'},
            {'codigo': 4, 'nombre': 'Rechazada', 'descripcion': 'Observación rechazada o no procede'},
        ]

        for estado_data in estados:
            estado, created = EstadoObservacion.objects.get_or_create(
                codigo=estado_data['codigo'],
                defaults={'nombre': estado_data['nombre'], 'descripcion': estado_data['descripcion']}
            )
            if created:
                self.stdout.write(f'Creado estado: {estado.nombre}')

        self.stdout.write(self.style.SUCCESS('Datos de incidencias cargados correctamente'))
