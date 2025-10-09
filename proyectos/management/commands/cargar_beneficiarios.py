from django.core.management.base import BaseCommand
from proyectos.models import Vivienda, Beneficiario

class Command(BaseCommand):
    help = 'Crear Beneficiario desde Vivienda.familia_beneficiaria y asignar en campo beneficiario (dry-run por defecto)'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Aplicar los cambios en la DB. Si no se pasa, solo dry-run')

    def handle(self, *args, **options):
        apply_changes = options.get('apply', False)
        viviendas = Vivienda.objects.filter(beneficiario__isnull=True).exclude(familia_beneficiaria__isnull=True).exclude(familia_beneficiaria__exact='')

        total = viviendas.count()
        self.stdout.write(f'Viviendas sin beneficiario y con nombre familia: {total}')

        creados = 0
        asignados = 0
        for v in viviendas:
            nombre = v.familia_beneficiaria.strip()
            if not nombre:
                continue
            # Buscar beneficiario existente por nombre exacto
            b = Beneficiario.objects.filter(nombre__iexact=nombre).first()
            if not b:
                creados += 1
                if apply_changes:
                    b = Beneficiario.objects.create(nombre=nombre)
                    self.stdout.write(f'Beneficiario creado: {b}')
                else:
                    self.stdout.write(f'[dry-run] Se crearía Beneficiario: {nombre}')
            if b:
                asignados += 1
                if apply_changes:
                    v.beneficiario = b
                    v.save()
                    self.stdout.write(f'Asignado beneficiario {b} a vivienda {v}')
                else:
                    self.stdout.write(f'[dry-run] Se asignaría beneficiario {b} a vivienda {v}')

        self.stdout.write(f'Resumen - creados: {creados}, asignados: {asignados} (apply={apply_changes})')
