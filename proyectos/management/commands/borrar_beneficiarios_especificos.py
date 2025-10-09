from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from proyectos.models import Beneficiario

class Command(BaseCommand):
    help = 'Borra beneficiarios específicos de la base de datos.'

    def add_arguments(self, parser):
        parser.add_argument(
            'nombres',
            nargs='+',
            type=str,
            help='Uno o más nombres de beneficiarios a borrar (entre comillas si tienen espacios).'
        )
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Aplica los cambios en la base de datos. Sin este flag, solo simula la operación.'
        )
        parser.add_argument(
            '--case-sensitive',
            action='store_true',
            help='Realiza la búsqueda de nombres distinguiendo mayúsculas y minúsculas.'
        )

    def handle(self, *args, **options):
        nombres_a_borrar = options['nombres']
        is_dry_run = not options['apply']
        case_sensitive = options['case_sensitive']

        if is_dry_run:
            self.stdout.write(self.style.WARNING("Modo DRY-RUN: No se realizarán cambios en la base de datos."))

        query_filter = 'nombre__in' if case_sensitive else 'nombre__iexact'
        
        beneficiarios_a_eliminar = Beneficiario.objects.none()
        
        # Para búsquedas insensibles a mayúsculas, necesitamos iterar si hay varios nombres
        if not case_sensitive:
            for nombre in nombres_a_borrar:
                 beneficiarios_a_eliminar |= Beneficiario.objects.filter(nombre__iexact=nombre)
        else:
            beneficiarios_a_eliminar = Beneficiario.objects.filter(nombre__in=nombres_a_borrar)

        count = beneficiarios_a_eliminar.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS(f"No se encontraron beneficiarios con los nombres especificados: {', '.join(nombres_a_borrar)}"))
            return

        self.stdout.write(f"Se encontraron {count} beneficiarios para eliminar:")
        for b in beneficiarios_a_eliminar:
            self.stdout.write(f"  - ID: {b.id}, Nombre: '{b.nombre}', RUT: '{b.rut}'")

        if is_dry_run:
            self.stdout.write(self.style.WARNING("\nPara borrar estos registros, ejecuta el comando de nuevo con el flag --apply."))
        else:
            try:
                with transaction.atomic():
                    self.stdout.write(self.style.WARNING("\nProcediendo a borrar..."))
                    deleted_count, _ = beneficiarios_a_eliminar.delete()
                    self.stdout.write(self.style.SUCCESS(f"\n¡Éxito! Se han eliminado {deleted_count} registros de la base de datos."))
            except Exception as e:
                raise CommandError(f"Ocurrió un error durante la eliminación. No se aplicaron cambios. Error: {e}")
