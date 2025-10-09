from django.core.management.base import BaseCommand
from proyectos.models import Beneficiario, Vivienda

class Command(BaseCommand):
    help = 'Eliminar beneficiario con nombre "nan" y desvincular viviendas asociadas'

    def handle(self, *args, **options):
        b = Beneficiario.objects.filter(nombre__iexact='nan').first()
        if not b:
            self.stdout.write('No se encontró beneficiario "nan"')
            return
        vs = list(Vivienda.objects.filter(beneficiario=b))
        self.stdout.write(f'Viviendas a desvincular: {len(vs)}')
        for v in vs:
            v.beneficiario = None
            v.save()
        b.delete()
        self.stdout.write('Beneficiario "nan" eliminado y viviendas desvinculadas')
