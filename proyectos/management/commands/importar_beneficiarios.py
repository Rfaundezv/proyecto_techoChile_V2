import csv
import pandas as pd
from django.core.management.base import BaseCommand

from proyectos.models import Beneficiario
from core.validators import clean_rut


class Command(BaseCommand):
    """Importar beneficiarios desde un archivo Excel.

    Dry-run por defecto. Opciones:
      - --apply: aplicar cambios a la base de datos
      - --create-missing: crear beneficiarios faltantes (solo con --apply)
      - --sheet: nombre o índice de la hoja
      - --dry-run-output <csv>: ruta para volcar auditoría
    """

    help = 'Importar nombre y RUT de beneficiarios desde un Excel. Dry-run por defecto.'

    def add_arguments(self, parser):
        parser.add_argument('archivo', help='Ruta al archivo Excel (.xlsx) con los datos')
        parser.add_argument('--sheet', default=0, help='Nombre o índice de la hoja (por defecto 0)')
        parser.add_argument('--apply', action='store_true', help='Aplicar los cambios a la base de datos')
        parser.add_argument('--create-missing', action='store_true', help='Crear beneficiarios que no existan (solo si --apply)')
        parser.add_argument('--dry-run-output', type=str, help='Ruta de archivo CSV para volcar el dry-run (auditoría)')

    def handle(self, *args, **options):
        archivo = options['archivo']
        sheet = options['sheet']
        apply_changes = options['apply']
        create_missing = options.get('create_missing', False)
        dry_run_output = options.get('dry_run_output')

        try:
            df = pd.read_excel(archivo, sheet_name=sheet)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error leyendo Excel: {e}'))
            return

        # normalizar columnas
        cols_map = {c: c.strip().lower() for c in df.columns}
        df.rename(columns=cols_map, inplace=True)

        # detectar columnas heurísticamente (nombre y rut de beneficiario)
        col_ben_nom = None
        col_ben_rut = None
        for c in df.columns:
            lc = c.lower()
            if any(x in lc for x in ('benef', 'beneficiario', 'vda', 'famil', 'nombre')) and 'rut' not in lc and 'tel' not in lc:
                col_ben_nom = col_ben_nom or c
            if 'rut' in lc and any(x in lc for x in ('benef', 'beneficiario', 'vda', 'famil')):
                col_ben_rut = col_ben_rut or c

        if not any([col_ben_nom, col_ben_rut]):
            self.stderr.write(self.style.ERROR('No se encontraron columnas de beneficiario reconocibles en el Excel.'))
            return

        total_rows = len(df)
        updated = 0
        created = 0
        skipped = 0
        all_actions = []

        def norm(v):
            if pd.isna(v):
                return ''
            return str(v).strip()

        for idx, row in df.iterrows():
            rownum = idx + 2
            ben_name = norm(row.get(col_ben_nom)) if col_ben_nom else ''
            ben_rut_raw = norm(row.get(col_ben_rut)) if col_ben_rut else ''

            ben_rut_clean = ''
            if ben_rut_raw:
                try:
                    ben_rut_clean = clean_rut(ben_rut_raw)
                except Exception:
                    ben_rut_clean = ben_rut_raw

            benef = None
            # buscar por RUT primero
            if ben_rut_clean:
                qs = Beneficiario.objects.filter(rut__iexact=ben_rut_clean)
                if qs.exists():
                    benef = qs.first()

            # fallback por nombre (único)
            if not benef and ben_name:
                qs = Beneficiario.objects.filter(nombre__iexact=ben_name)
                if qs.count() == 1:
                    benef = qs.first()
                elif qs.count() > 1:
                    self.stdout.write(self.style.WARNING(f'Fila {rownum}: nombre beneficiario "{ben_name}" es ambiguo ({qs.count()} coincidencias).'))
                    skipped += 1

            if benef:
                old_name = benef.nombre
                old_rut = benef.rut
                new_name = ben_name or old_name
                new_rut = ben_rut_clean or old_rut
                changed = False
                if new_name and (not old_name or old_name.strip() != new_name.strip()):
                    changed = True
                if new_rut and (not old_rut or (old_rut and old_rut.strip().lower() != new_rut.strip().lower())):
                    changed = True

                if changed:
                    all_actions.append({'row': rownum, 'action': 'update_benef', 'object': 'beneficiario', 'object_id': benef.id, 'old_name': old_name, 'old_rut': old_rut, 'new_name': new_name, 'new_rut': new_rut, 'message': f'update_benef id={benef.id} name "{old_name}"->{new_name} rut {old_rut}->{new_rut}'})
                    if apply_changes:
                        benef.nombre = new_name
                        if new_rut:
                            benef.rut = new_rut
                        benef.save()
                        updated += 1
                else:
                    all_actions.append({'row': rownum, 'action': 'no_change_benef', 'object': 'beneficiario', 'object_id': benef.id, 'old_name': old_name, 'old_rut': old_rut, 'new_name': new_name, 'new_rut': new_rut, 'message': 'no_change_benef'})
            else:
                # no existe
                if ben_rut_clean and create_missing:
                    all_actions.append({'row': rownum, 'action': 'create_benef', 'object': 'beneficiario', 'object_id': None, 'old_name': None, 'old_rut': None, 'new_name': ben_name, 'new_rut': ben_rut_clean, 'message': f'create_benef name="{ben_name}" rut={ben_rut_clean}'})
                    if apply_changes:
                        Beneficiario.objects.create(nombre=ben_name or ben_rut_clean, rut=ben_rut_clean)
                        created += 1
                else:
                    if ben_name or ben_rut_clean:
                        all_actions.append({'row': rownum, 'action': 'benef_not_found', 'object': 'beneficiario', 'object_id': None, 'old_name': None, 'old_rut': None, 'new_name': ben_name, 'new_rut': ben_rut_clean, 'message': 'benef_not_found'})
                        skipped += 1

        # volcar CSV
        if dry_run_output:
            try:
                with open(dry_run_output, 'w', newline='', encoding='utf-8') as fh:
                    fieldnames = ['row', 'action', 'object', 'object_id', 'old_name', 'old_rut', 'new_name', 'new_rut', 'message']
                    writer = csv.DictWriter(fh, fieldnames=fieldnames)
                    writer.writeheader()
                    for r in all_actions:
                        writer.writerow(r)
                self.stdout.write(self.style.SUCCESS(f'Dry-run CSV escrito en: {dry_run_output}'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Error escribiendo CSV de dry-run: {e}'))

        # resumen
        self.stdout.write('\nResumen:')
        self.stdout.write(f'  Filas leídas: {total_rows}')
        self.stdout.write(f'  Beneficiarios actualizados: {updated}')
        self.stdout.write(f'  Beneficiarios creados: {created}')
        self.stdout.write(f'  Filas omitidas/ambiguas: {skipped}')
        if not apply_changes:
            self.stdout.write(self.style.WARNING('\nModo dry-run: no se aplicaron cambios. Ejecute con --apply para persistir.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nCambios aplicados con --apply.'))
