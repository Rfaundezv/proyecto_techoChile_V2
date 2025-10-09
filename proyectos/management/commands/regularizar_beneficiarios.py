import sys
import pandas as pd
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from proyectos.models import Beneficiario
from unidecode import unidecode

def normalize_text(text):
    """Normaliza el texto para comparación: sin tildes y en minúsculas."""
    if not isinstance(text, str):
        return ""
    return unidecode(text).lower().strip()

class Command(BaseCommand):
    help = 'Regulariza la tabla de Beneficiarios usando un CSV como fuente de verdad.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Ruta al archivo CSV con los datos de los beneficiarios.')
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Aplica los cambios en la base de datos. Sin este flag, solo simula la operación.'
        )

    def handle(self, *args, **options):
        csv_path = Path(options['csv_file'])
        is_dry_run = not options['apply']

        if not csv_path.exists():
            raise CommandError(f"El archivo '{csv_path}' no existe.")

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            raise CommandError(f"Error al leer el archivo CSV: {e}")

        required_cols = ['nombre', 'rut_limpio']
        if not all(col in df.columns for col in required_cols):
            raise CommandError(f"El CSV debe contener las columnas: {required_cols}. Columnas encontradas: {df.columns.tolist()}")

        self.stdout.write(self.style.SUCCESS(f"Procesando {len(df)} filas desde '{csv_path.name}'..."))
        if is_dry_run:
            self.stdout.write(self.style.WARNING("Modo DRY-RUN: No se realizarán cambios en la base de datos."))

        summary = {'updated': 0, 'not_found': 0, 'ambiguous': 0, 'no_change': 0, 'errors': 0}

        # Crear un mapa de nombres normalizados a beneficiarios de la DB
        db_beneficiarios = list(Beneficiario.objects.all())
        beneficiarios_map = {}
        for b in db_beneficiarios:
            normalized_name = normalize_text(b.nombre)
            if normalized_name not in beneficiarios_map:
                beneficiarios_map[normalized_name] = []
            beneficiarios_map[normalized_name].append(b)

        try:
            with transaction.atomic():
                for index, row in df.iterrows():
                    csv_nombre = row['nombre']
                    csv_rut = row['rut_limpio']
                    
                    if pd.isna(csv_nombre) or pd.isna(csv_rut):
                        self.stdout.write(self.style.ERROR(f"Fila {index+2}: Nombre o RUT vacío, se omite."))
                        summary['errors'] += 1
                        continue

                    normalized_csv_nombre = normalize_text(csv_nombre)
                    
                    matches = beneficiarios_map.get(normalized_csv_nombre, [])

                    if len(matches) == 0:
                        self.stdout.write(f"NO ENCONTRADO: '{csv_nombre}' no se encontró en la base de datos.")
                        summary['not_found'] += 1
                    elif len(matches) > 1:
                        self.stdout.write(self.style.WARNING(f"AMBIGUO: '{csv_nombre}' tiene {len(matches)} coincidencias en la DB. Se omite."))
                        summary['ambiguous'] += 1
                    else:
                        beneficiario = matches[0]
                        if beneficiario.rut == csv_rut:
                            summary['no_change'] += 1
                        else:
                            self.stdout.write(f"ACTUALIZAR: '{beneficiario.nombre}' (ID: {beneficiario.id}) - RUT: '{beneficiario.rut}' -> '{csv_rut}'")
                            beneficiario.rut = csv_rut
                            if not is_dry_run:
                                beneficiario.save()
                            summary['updated'] += 1
                
                if not is_dry_run:
                    self.stdout.write(self.style.SUCCESS("\nCambios aplicados a la base de datos."))
                else:
                    # Si es dry-run, forzamos un rollback para no confirmar la transacción
                    transaction.set_rollback(True)

        except Exception as e:
            raise CommandError(f"\nOcurrió un error durante la transacción. No se aplicaron cambios. Error: {e}")

        self.stdout.write(self.style.SUCCESS("\n--- Resumen de la operación ---"))
        self.stdout.write(f"Beneficiarios a actualizar: {summary['updated']}")
        self.stdout.write(f"Sin cambios (RUT ya coincide): {summary['no_change']}")
        self.stdout.write(f"No encontrados en la DB: {summary['not_found']}")
        self.stdout.write(f"Nombres ambiguos (omitidos): {summary['ambiguous']}")
        self.stdout.write(f"Filas con errores en CSV: {summary['errors']}")
        self.stdout.write("---------------------------------")
