from django.core.management.base import BaseCommand
from core.models import Region, Comuna

class Command(BaseCommand):
    help = 'Corrige el nombre de la Región Metropolitana y asegura que Santiago esté como comuna'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Iniciando corrección de Región Metropolitana...'))
        
        # Buscar la región metropolitana (puede tener varios nombres)
        region_metro = None
        nombres_posibles = [
            'Metropolitana de Santiago',
            'Región Metropolitana de Santiago',
            'RM',
            'Región Metropolitana'
        ]
        
        for nombre in nombres_posibles:
            region = Region.objects.filter(nombre__icontains=nombre).first()
            if region:
                region_metro = region
                self.stdout.write(f'✓ Región encontrada: "{region.nombre}" (ID: {region.id})')
                break
        
        if not region_metro:
            self.stdout.write(
                self.style.ERROR('❌ No se encontró la Región Metropolitana')
            )
            return
        
        # Cambiar el nombre a "Región Metropolitana"
        nombre_anterior = region_metro.nombre
        region_metro.nombre = 'Región Metropolitana'
        region_metro.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Nombre actualizado: "{nombre_anterior}" → "Región Metropolitana"'
            )
        )
        
        # Verificar si existe la comuna Santiago
        comuna_santiago = Comuna.objects.filter(
            region=region_metro,
            nombre__iexact='Santiago'
        ).first()
        
        if comuna_santiago:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ La comuna "Santiago" ya existe en la Región Metropolitana (ID: {comuna_santiago.id})'
                )
            )
        else:
            # Crear la comuna Santiago
            comuna_santiago = Comuna.objects.create(
                region=region_metro,
                nombre='Santiago'
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Comuna "Santiago" creada en la Región Metropolitana (ID: {comuna_santiago.id})'
                )
            )
        
        # Mostrar todas las comunas de la Región Metropolitana
        comunas = Comuna.objects.filter(region=region_metro).order_by('nombre')
        self.stdout.write(f'\n📋 Comunas de la Región Metropolitana ({comunas.count()} total):')
        for comuna in comunas:
            self.stdout.write(f'  • {comuna.nombre}')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS('\n✅ Corrección completada exitosamente!')
        )
        self.stdout.write('='*60)
