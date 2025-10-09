
from django.core.management.base import BaseCommand
from proyectos.models import TipologiaVivienda, Recinto

class Command(BaseCommand):
    help = 'Carga tipologías de vivienda y recintos básicos'

    def handle(self, *args, **kwargs):
        tipologias = [
            {'codigo': 1, 'nombre': 'Casa Básica 42m²', 'descripcion': 'Casa básica de 1 dormitorio'},
            {'codigo': 2, 'nombre': 'Casa 2 Dormitorios 55m²', 'descripcion': 'Casa de 2 dormitorios'},
            {'codigo': 3, 'nombre': 'Casa 3 Dormitorios 70m²', 'descripcion': 'Casa de 3 dormitorios'},
        ]

        recintos_por_tipologia = {
            1: [  # Casa básica
                {'codigo': '01', 'nombre': 'Estar-Comedor', 'elementos': ['Pintura', 'Piso', 'Ventanas', 'Puertas']},
                {'codigo': '02', 'nombre': 'Cocina', 'elementos': ['Muebles', 'Encimera', 'Grifería', 'Azulejos']},
                {'codigo': '03', 'nombre': 'Dormitorio', 'elementos': ['Pintura', 'Piso', 'Ventana', 'Closet']},
                {'codigo': '04', 'nombre': 'Baño', 'elementos': ['Azulejos', 'Sanitarios', 'Grifería', 'Ventilación']},
            ],
            2: [  # 2 dormitorios
                {'codigo': '01', 'nombre': 'Estar-Comedor', 'elementos': ['Pintura', 'Piso', 'Ventanas', 'Puertas']},
                {'codigo': '02', 'nombre': 'Cocina', 'elementos': ['Muebles', 'Encimera', 'Grifería', 'Azulejos']},
                {'codigo': '03', 'nombre': 'Dormitorio Principal', 'elementos': ['Pintura', 'Piso', 'Ventana', 'Closet']},
                {'codigo': '04', 'nombre': 'Dormitorio 2', 'elementos': ['Pintura', 'Piso', 'Ventana', 'Closet']},
                {'codigo': '05', 'nombre': 'Baño', 'elementos': ['Azulejos', 'Sanitarios', 'Grifería', 'Ventilación']},
                {'codigo': '06', 'nombre': 'Patio', 'elementos': ['Piso', 'Muros', 'Desagües']},
            ],
            3: [  # 3 dormitorios
                {'codigo': '01', 'nombre': 'Estar-Comedor', 'elementos': ['Pintura', 'Piso', 'Ventanas', 'Puertas']},
                {'codigo': '02', 'nombre': 'Cocina', 'elementos': ['Muebles', 'Encimera', 'Grifería', 'Azulejos']},
                {'codigo': '03', 'nombre': 'Dormitorio Principal', 'elementos': ['Pintura', 'Piso', 'Ventana', 'Closet']},
                {'codigo': '04', 'nombre': 'Dormitorio 2', 'elementos': ['Pintura', 'Piso', 'Ventana', 'Closet']},
                {'codigo': '05', 'nombre': 'Dormitorio 3', 'elementos': ['Pintura', 'Piso', 'Ventana', 'Closet']},
                {'codigo': '06', 'nombre': 'Baño', 'elementos': ['Azulejos', 'Sanitarios', 'Grifería', 'Ventilación']},
                {'codigo': '07', 'nombre': 'Patio', 'elementos': ['Piso', 'Muros', 'Desagües']},
            ]
        }

        for tip_data in tipologias:
            tipologia, created = TipologiaVivienda.objects.get_or_create(
                codigo=tip_data['codigo'],
                defaults={'nombre': tip_data['nombre'], 'descripcion': tip_data['descripcion']}
            )
            if created:
                self.stdout.write(f'Creada tipología: {tipologia.nombre}')

            # Crear recintos para esta tipología
            recintos = recintos_por_tipologia.get(tip_data['codigo'], [])
            for recinto_data in recintos:
                recinto, r_created = Recinto.objects.get_or_create(
                    tipologia=tipologia,
                    codigo=recinto_data['codigo'],
                    defaults={
                        'nombre': recinto_data['nombre'],
                        'elementos_disponibles': recinto_data['elementos']
                    }
                )
                if r_created:
                    self.stdout.write(f'  Creado recinto: {recinto.nombre}')

        self.stdout.write(self.style.SUCCESS('Tipologías y recintos cargados correctamente'))
