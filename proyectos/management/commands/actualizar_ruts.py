import csv
import pandas as pd
from django.core.management.base import BaseCommand

from proyectos.models import Beneficiario
from core.models import Constructora
from core.validators import clean_rut


class Command(BaseCommand):
    """Management command: actualizar_ruts

    Lee un Excel y propone/actualiza los RUTs de Beneficiarios y Constructoras.
    Dry-run por defecto. Opciones:
      - --apply: aplica los cambios
      - --create-missing: crea registros faltantes (solo con --apply)
      - --dry-run-output <csv>: escribe un CSV con las propuestas
    """

    help = 'Actualizar RUTs de Beneficiarios y Constructoras desde un archivo Excel. Dry-run por defecto.'

    def add_arguments(self, parser):
        parser.add_argument('archivo', help='Ruta al archivo Excel (.xlsx) con los datos')
        parser.add_argument('--sheet', default=0, help='Nombre o índice de la hoja (por defecto 0)')
        parser.add_argument('--apply', action='store_true', help='Aplicar los cambios a la base de datos')
        parser.add_argument('--create-missing', action='store_true', help='Crear beneficiarios o constructoras que no existan (solo si --apply)')
        parser.add_argument('--dry-run-output', type=str, help='Ruta de archivo CSV para volcar el dry-run (propuestas)')

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

        # detectar columnas heurísticamente
        col_ben_nom = None
        col_ben_rut = None
        col_cons_nom = None
        col_cons_rut = None

        for c in df.columns:
            lc = c.lower()
            if any(x in lc for x in ('benef', 'beneficiario', 'vda', 'famil')) and 'rut' not in lc and 'tel' not in lc:
                col_ben_nom = col_ben_nom or c
            if 'rut' in lc and any(x in lc for x in ('benef', 'beneficiario', 'vda', 'famil')):
                col_ben_rut = col_ben_rut or c
            if any(x in lc for x in ('construct', 'empresa', 'constructor')) and 'rut' not in lc:
                col_cons_nom = col_cons_nom or c
            if 'rut' in lc and any(x in lc for x in ('construct', 'empresa', 'constructor')):
                col_cons_rut = col_cons_rut or c

        if not any([col_ben_nom, col_ben_rut, col_cons_nom, col_cons_rut]):
            self.stderr.write(self.style.ERROR('No se encontraron columnas reconocibles en el Excel.'))
            return

        total_rows = len(df)
        updated_benef = 0
        updated_cons = 0
        skipped = 0
        all_actions = []

        def norm(v):
            if pd.isna(v):
                return ''
            return str(v).strip()

        for idx, row in df.iterrows():
            rownum = idx + 2
            actions = []

            ben_name = norm(row.get(col_ben_nom)) if col_ben_nom else ''
            ben_rut_raw = norm(row.get(col_ben_rut)) if col_ben_rut else ''
            cons_name = norm(row.get(col_cons_nom)) if col_cons_nom else ''
            cons_rut_raw = norm(row.get(col_cons_rut)) if col_cons_rut else ''

            ben_rut_clean = ''
            if ben_rut_raw:
                try:
                    ben_rut_clean = clean_rut(ben_rut_raw)
                except Exception:
                    ben_rut_clean = ben_rut_raw

            cons_rut_clean = ''
            if cons_rut_raw:
                try:
                    cons_rut_clean = clean_rut(cons_rut_raw)
                except Exception:
                    cons_rut_clean = cons_rut_raw

            # beneficiario: buscar por RUT primero
            benef = None
            if ben_rut_clean:
                qs = Beneficiario.objects.filter(rut__iexact=ben_rut_clean)
                if qs.exists():
                    benef = qs.first()

            if not benef and ben_name:
                qs = Beneficiario.objects.filter(nombre__iexact=ben_name)
                if qs.count() == 1:
                    benef = qs.first()
                elif qs.count() > 1:
                    self.stdout.write(self.style.WARNING(f'Fila {rownum}: nombre beneficiario "{ben_name}" es ambiguo ({qs.count()} coincidencias).'))
                    skipped += 1

            if benef:
                if ben_rut_clean and (not benef.rut or benef.rut.strip() != ben_rut_clean):
                    actions.append({'action': 'update_benef', 'object': 'beneficiario', 'object_id': benef.id, 'old_rut': benef.rut, 'new_rut': ben_rut_clean, 'name': benef.nombre})
                    if apply_changes:
                        benef.rut = ben_rut_clean
                        benef.save()
                        updated_benef += 1
                else:
                    actions.append({'action': 'no_change_benef', 'object': 'beneficiario', 'object_id': benef.id, 'old_rut': benef.rut, 'new_rut': ben_rut_clean, 'name': benef.nombre})
            else:
                if ben_rut_clean and create_missing:
                    actions.append({'action': 'create_benef', 'object': 'beneficiario', 'object_id': None, 'old_rut': None, 'new_rut': ben_rut_clean, 'name': ben_name})
                    if apply_changes:
                        Beneficiario.objects.create(nombre=ben_name or ben_rut_clean, rut=ben_rut_clean)
                        updated_benef += 1
                else:
                    if ben_name or ben_rut_clean:
                        actions.append({'action': 'benef_not_found', 'object': 'beneficiario', 'object_id': None, 'old_rut': None, 'new_rut': ben_rut_clean, 'name': ben_name})
                        skipped += 1

            # constructora: buscar por RUT primero
            cons = None
            if cons_rut_clean:
                qs = Constructora.objects.filter(rut__iexact=cons_rut_clean)
                if qs.exists():
                    cons = qs.first()

            if not cons and cons_name:
                qs = Constructora.objects.filter(nombre__iexact=cons_name)
                if qs.count() == 1:
                    cons = qs.first()
                elif qs.count() > 1:
                    self.stdout.write(self.style.WARNING(f'Fila {rownum}: nombre constructora "{cons_name}" es ambiguo ({qs.count()} coincidencias).'))
                    skipped += 1

            if cons:
                if cons_rut_clean and (not cons.rut or cons.rut.strip() != cons_rut_clean):
                    actions.append({'action': 'update_cons', 'object': 'constructora', 'object_id': cons.id, 'old_rut': cons.rut, 'new_rut': cons_rut_clean, 'name': cons.nombre})
                    if apply_changes:
                        cons.rut = cons_rut_clean
                        cons.save()
                        updated_cons += 1
                else:
                    actions.append({'action': 'no_change_cons', 'object': 'constructora', 'object_id': cons.id, 'old_rut': cons.rut, 'new_rut': cons_rut_clean, 'name': cons.nombre})
            else:
                if cons_rut_clean and create_missing:
                    actions.append({'action': 'create_cons', 'object': 'constructora', 'object_id': None, 'old_rut': None, 'new_rut': cons_rut_clean, 'name': cons_name})
                    if apply_changes:
                        Constructora.objects.create(nombre=cons_name or cons_rut_clean, rut=cons_rut_clean)
                        updated_cons += 1
                else:
                    if cons_name or cons_rut_clean:
                        actions.append({'action': 'cons_not_found', 'object': 'constructora', 'object_id': None, 'old_rut': None, 'new_rut': cons_rut_clean, 'name': cons_name})
                        skipped += 1

            if actions:
                self.stdout.write(self.style.SUCCESS(f'Fila {rownum} acciones:'))
                for a in actions:
                    msg = f"{a['action']}: {a['object']} id={a.get('object_id')} name={a.get('name')} old={a.get('old_rut')} new={a.get('new_rut')}"
                    self.stdout.write(f'  - {msg}')
                    all_actions.append({'row': rownum, 'action': a['action'], 'object': a['object'], 'object_id': a.get('object_id'), 'name': a.get('name'), 'old_rut': a.get('old_rut'), 'new_rut': a.get('new_rut'), 'message': msg})

        # volcar CSV
        if dry_run_output:
            try:
                with open(dry_run_output, 'w', newline='', encoding='utf-8') as fh:
                    writer = csv.DictWriter(fh, fieldnames=['row', 'action', 'object', 'object_id', 'name', 'old_rut', 'new_rut', 'message'])
                    writer.writeheader()
                    for r in all_actions:
                        writer.writerow(r)
                self.stdout.write(self.style.SUCCESS(f'Dry-run CSV escrito en: {dry_run_output}'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Error escribiendo CSV de dry-run: {e}'))

        # resumen
        self.stdout.write('\nResumen:')
        self.stdout.write(f'  Filas leídas: {total_rows}')
        self.stdout.write(f'  Beneficiarios actualizados: {updated_benef}')
        self.stdout.write(f'  Constructoras actualizadas: {updated_cons}')
        self.stdout.write(f'  Filas omitidas/ambiguas: {skipped}')
        if not apply_changes:
            self.stdout.write(self.style.WARNING('\nModo dry-run: no se aplicaron cambios. Ejecute con --apply para persistir.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nCambios aplicados con --apply.'))
