from django.core.management.base import BaseCommand
from proyectos.models import Recinto, TipologiaVivienda
import pandas as pd
import os

class Command(BaseCommand):
    help = 'Carga o actualiza recintos desde el archivo Excel Base-central-de-observaciones-de-postventa-sin-filtro.xlsx'

    def add_arguments(self, parser):
        parser.add_argument(
            '--archivo',
            type=str,
            default='Base-central-de-observaciones-de-postventa-sin-filtro.xlsx',
            help='Nombre del archivo Excel a importar'
        )
        parser.add_argument(
            '--sobrescribir',
            action='store_true',
            help='Sobrescribir elementos existentes en lugar de agregar'
        )

    def handle(self, *args, **options):
        archivo = options['archivo']
        sobrescribir = options['sobrescribir']
        
        # Buscar el archivo en el directorio actual o en la raíz del proyecto
        posibles_rutas = [
            archivo,
            os.path.join(os.getcwd(), archivo),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), archivo),
        ]
        
        ruta_archivo = None
        for ruta in posibles_rutas:
            if os.path.exists(ruta):
                ruta_archivo = ruta
                break
        
        if not ruta_archivo:
            self.stdout.write(
                self.style.ERROR(f'❌ No se encontró el archivo: {archivo}')
            )
            self.stdout.write('\nBusca el archivo en:')
            for ruta in posibles_rutas:
                self.stdout.write(f'  - {ruta}')
            return
        
        self.stdout.write(f'📂 Archivo encontrado: {ruta_archivo}')
        
        try:
            # Leer el archivo Excel con codificación correcta
            self.stdout.write('📖 Leyendo archivo Excel...')
            df = pd.read_excel(ruta_archivo, engine='openpyxl')
            
            # Función para limpiar caracteres mal codificados
            def limpiar_texto(texto):
                if pd.isna(texto) or not isinstance(texto, str):
                    return texto
                # Reemplazar caracteres mal codificados comunes
                replacements = {
                    'Ã³': 'ó',
                    'Ã¡': 'á',
                    'Ã©': 'é',
                    'Ã­': 'í',
                    'Ãº': 'ú',
                    'Ã±': 'ñ',
                    'Â': '',
                }
                for mal, bien in replacements.items():
                    texto = texto.replace(mal, bien)
                return texto
            
            # Limpiar todas las columnas de texto
            for col in df.columns:
                if df[col].dtype == 'object':  # Solo para columnas de texto
                    df[col] = df[col].apply(limpiar_texto)
            
            # Mostrar las columnas disponibles
            self.stdout.write(f'\n📋 Columnas encontradas: {list(df.columns)}\n')
            
            # Buscar columnas relevantes (ajustar según estructura real del Excel)
            columnas_necesarias = ['tipologia', 'nombre', 'descripcion', 'elementos_disponibles']
            
            # Intentar identificar columnas por similitud de nombres
            col_tipologia = None
            col_nombre = None
            col_elementos = None
            
            for col in df.columns:
                col_lower = str(col).lower()
                if 'vda_tipologia' in col_lower or col == 'VDA_TIPOLOGIA':
                    col_tipologia = col
                elif 'recinto_nombre' in col_lower or col == 'RECINTO_NOMBRE':
                    col_nombre = col
                elif 'pv_elemento' in col_lower or col == 'PV_ELEMENTO':
                    col_elementos = col
            
            if not all([col_tipologia, col_nombre, col_elementos]):
                self.stdout.write(
                    self.style.WARNING(
                        '\n⚠️  No se pudieron identificar automáticamente las columnas.'
                    )
                )
                self.stdout.write('\nPor favor indica manualmente:')
                self.stdout.write(f'  Tipología: {col_tipologia}')
                self.stdout.write(f'  Nombre recinto: {col_nombre}')
                self.stdout.write(f'  Elementos: {col_elementos}')
                
                # Mostrar vista previa de los datos
                self.stdout.write('\n📊 Vista previa de los datos:')
                self.stdout.write(str(df.head()))
                return
            
            self.stdout.write(f'\n✅ Columnas identificadas:')
            self.stdout.write(f'  - Tipología: {col_tipologia}')
            self.stdout.write(f'  - Recinto: {col_nombre}')
            self.stdout.write(f'  - Elementos: {col_elementos}')
            
            # Procesar datos
            recintos_actualizados = 0
            recintos_creados = 0
            elementos_agregados = 0
            
            # Agrupar por tipología y nombre de recinto
            for (tipologia_nombre, recinto_nombre), grupo in df.groupby([col_tipologia, col_nombre]):
                self.stdout.write(f'\n🔄 Procesando: {tipologia_nombre} - {recinto_nombre}')
                
                # Buscar la tipología - primero intentar por código exacto, luego por nombre
                tipologia = None
                
                # Intentar convertir a int (código)
                try:
                    codigo_tipologia = int(tipologia_nombre)
                    tipologia = TipologiaVivienda.objects.filter(codigo=codigo_tipologia).first()
                except (ValueError, TypeError):
                    pass
                
                # Si no se encontró por código, buscar por nombre exacto
                if not tipologia:
                    tipologia = TipologiaVivienda.objects.filter(nombre__iexact=str(tipologia_nombre)).first()
                
                # Si aún no se encontró, buscar por nombre contenido
                if not tipologia:
                    tipologias = TipologiaVivienda.objects.filter(nombre__icontains=str(tipologia_nombre))
                    if tipologias.count() == 1:
                        tipologia = tipologias.first()
                    elif tipologias.count() > 1:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ⚠️  Múltiples tipologías encontradas para "{tipologia_nombre}": {list(tipologias.values_list("nombre", flat=True))}'
                            )
                        )
                        # Usar la primera
                        tipologia = tipologias.first()
                        self.stdout.write(f'  ℹ️  Usando: {tipologia.nombre}')
                
                if not tipologia:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️  Tipología no encontrada: {tipologia_nombre} - SALTANDO')
                    )
                    continue
                
                # Obtener todos los elementos únicos para este recinto
                elementos = set()
                for _, row in grupo.iterrows():
                    if pd.notna(row[col_elementos]):
                        elemento = str(row[col_elementos]).strip()
                        if elemento:
                            elementos.add(elemento)
                
                elementos_lista = sorted(list(elementos))
                
                # Buscar o crear el recinto
                recinto, created = Recinto.objects.get_or_create(
                    tipologia=tipologia,
                    nombre=recinto_nombre,
                    defaults={
                        'codigo': f'R{Recinto.objects.filter(tipologia=tipologia).count() + 1:02d}',
                        'elementos_disponibles': elementos_lista
                    }
                )
                
                if created:
                    recintos_creados += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✅ Creado con {len(elementos_lista)} elementos'
                        )
                    )
                else:
                    # Actualizar elementos
                    if sobrescribir:
                        recinto.elementos_disponibles = elementos_lista
                        accion = 'sobrescritos'
                    else:
                        # Agregar nuevos elementos sin duplicar
                        elementos_existentes = set(recinto.elementos_disponibles or [])
                        elementos_antes = len(elementos_existentes)
                        elementos_existentes.update(elementos)
                        recinto.elementos_disponibles = sorted(list(elementos_existentes))
                        elementos_agregados += len(elementos_existentes) - elementos_antes
                        accion = f'+{len(elementos_existentes) - elementos_antes} agregados'
                    
                    recinto.save()
                    recintos_actualizados += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✅ Actualizado: {len(recinto.elementos_disponibles)} elementos ({accion})'
                        )
                    )
            
            # Resumen final
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('\n✅ IMPORTACIÓN COMPLETADA'))
            self.stdout.write(f'  📊 Recintos creados: {recintos_creados}')
            self.stdout.write(f'  🔄 Recintos actualizados: {recintos_actualizados}')
            if not sobrescribir:
                self.stdout.write(f'  ➕ Elementos nuevos agregados: {elementos_agregados}')
            self.stdout.write('='*60)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Error al procesar el archivo: {str(e)}')
            )
            import traceback
            self.stdout.write(traceback.format_exc())
