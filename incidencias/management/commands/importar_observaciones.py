from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_datetime
import pandas as pd
import os
from datetime import datetime
import traceback

from core.models import Region, Comuna, Constructora
# TipologiaVivienda en el proyecto se llama TipologiaVivienda -> alias como Tipologia
from proyectos.models import Proyecto, TipologiaVivienda as Tipologia, Vivienda, Recinto

# Obtener el modelo de usuario personalizado
User = get_user_model()
from incidencias.models import TipoObservacion, EstadoObservacion, Observacion

class Command(BaseCommand):
    help = 'Importa datos del Excel de observaciones de Techo Chile'

    def add_arguments(self, parser):
        parser.add_argument(
            '--archivo',
            type=str,
            default='Base-central-de-observaciones-de-postventa-sin-filtro.xlsx',
            help='Nombre del archivo Excel a importar'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la importación sin escribir en la base de datos'
        )

    def handle(self, *args, **options):
        archivo = options['archivo']
        dry_run = options.get('dry_run', False)

        if not os.path.exists(archivo):
            self.stdout.write(self.style.ERROR(f'El archivo {archivo} no existe'))
            return

        try:
            # Leer archivo Excel
            self.stdout.write('Leyendo archivo Excel...')
            df = pd.read_excel(archivo, sheet_name=0)
            self.stdout.write(f'Archivo leído: {len(df)} registros')

            # Crear datos base (si corresponde)
            self.crear_datos_base(dry_run=dry_run)

            # Importar datos (pasamos dry_run para simular)
            self.importar_proyectos(df, dry_run=dry_run)
            self.importar_viviendas(df, dry_run=dry_run)
            self.importar_recintos(df, dry_run=dry_run)
            self.importar_observaciones(df, dry_run=dry_run)

            self.stdout.write(self.style.SUCCESS('Importación completada exitosamente'))

        except Exception:
            tb = traceback.format_exc()
            self.stdout.write(self.style.ERROR('Error durante la importación:'))
            self.stdout.write(self.style.ERROR(tb))

    def crear_datos_base(self, dry_run=False):
        """Crear regiones, comunas, constructoras, estados, etc.
        Si dry_run=True solo reporta lo que se crearía sin escribir en la DB.
        """
        self.stdout.write('Creando datos base...')

        # Región
        if dry_run:
            self.stdout.write('[dry-run] Region que se crearía: codigo=05 nombre=Valparaíso')
            region = None
        else:
            region, _ = Region.objects.get_or_create(
                codigo='05',
                defaults={'nombre': 'Valparaíso'}
            )

        # Comuna
        if dry_run:
            self.stdout.write('[dry-run] Comuna que se crearía: codigo=05401 nombre=La Cruz')
            comuna = None
        else:
            comuna, _ = Comuna.objects.get_or_create(
                codigo='05401',
                defaults={'nombre': 'La Cruz', 'region': region}
            )

        # Constructora
        # La clase Constructora no tiene campo 'rut' en este proyecto; usar 'nombre'
        if dry_run:
            self.stdout.write('[dry-run] Constructora que se crearía: nombre=DYR')
            constructora = None
        else:
            constructora, _ = Constructora.objects.get_or_create(
                nombre='DYR',
                defaults={'direccion': '', 'activo': True, 'region': region, 'comuna': comuna}
            )

        # Crear usuario importador por defecto (se usará para proyectos y observaciones)
        # Crear usuario importador compatible con el modelo Usuario (email como identificador)
        usuario_import_email = 'import@techo.org'
        if dry_run:
            self.stdout.write('[dry-run] Usuario importador que se crearía: import@techo.org')
            usuario_import = None
        else:
            usuario_import = None
            try:
                usuario_import = User.objects.get(email=usuario_import_email)
            except Exception:
                # Si no existe, crear
                usuario_import, _ = User.objects.get_or_create(email=usuario_import_email, defaults={'nombre': 'Importador Techo'})

    def importar_proyectos(self, df, dry_run=False):
        """Importar proyectos únicos del Excel"""
        self.stdout.write('Importando proyectos...')

        # Obtener proyectos únicos
        proyectos_unicos = df[['PYTO_COD', 'PYTO_SIGLAS', 'PYTO_NOMBRE', 'CONSTRUCTORA', 'COMUNA', 'PYTO_S', 'PYTO_W']].drop_duplicates()

        # Intentar obtener la comuna por código (creada en crear_datos_base), si no existe, fallback por nombre
        try:
            comuna = Comuna.objects.get(codigo='05401')
        except Comuna.DoesNotExist:
            # Fallback: tomar la primera comuna llamada 'La Cruz'
            comuna_qs = Comuna.objects.filter(nombre='La Cruz')
            if comuna_qs.exists():
                comuna = comuna_qs.first()
            else:
                self.stdout.write(self.style.ERROR('Comuna La Cruz no encontrada'))
                return
        constructora = Constructora.objects.get(nombre='DYR')

        # Usuario importador (creado en crear_datos_base) - buscar por email
        try:
            usuario_import = User.objects.get(email='import@techo.org')
        except User.DoesNotExist:
            usuario_import = User.objects.create(email='import@techo.org', nombre='Importador Techo')

        for _, row in proyectos_unicos.iterrows():
            if pd.notna(row['PYTO_COD']) and pd.notna(row['PYTO_SIGLAS']):
                codigo = f"{int(row['PYTO_COD'])}-{row['PYTO_SIGLAS']}"

                # Evitar get_or_create porque puede forzar evaluación que cause errores de conversión
                proyecto_id = Proyecto.objects.filter(codigo=codigo).values_list('id', flat=True).first()
                proyecto = None
                if not proyecto_id:
                    if dry_run:
                        # Contabilizar que se crearía
                        self.stdout.write(f'[dry-run] Proyecto que se crearía: {codigo}')
                    else:
                        proyecto = Proyecto.objects.create(
                        codigo=codigo,
                        nombre=row['PYTO_NOMBRE'] or 'Proyecto Techo Chile',
                        siglas=str(row['PYTO_SIGLAS']) if pd.notna(row['PYTO_SIGLAS']) else '',
                        region=comuna.region,
                        comuna=comuna,
                        constructora=constructora,
                        coordenadas_s=(float(row['PYTO_S']) if pd.notna(row['PYTO_S']) else None),
                        coordenadas_w=(float(row['PYTO_W']) if pd.notna(row['PYTO_W']) else None),
                        activo=True,
                        fecha_entrega=datetime.now().date(),
                        creado_por=usuario_import
                    )
                        self.stdout.write(f'Proyecto creado: {codigo}')
                else:
                    # Evitar cargar la instancia completa (puede causar conversiones Decimal problemáticas)
                    proyecto = None

    def importar_viviendas(self, df, dry_run=False):
        """Importar viviendas únicas del Excel"""
        self.stdout.write('Importando viviendas...')

        # Obtener viviendas únicas
        viviendas_unicas = df[['PYTO_COD', 'PYTO_SIGLAS', 'VDA_CODIGO', 'VDA_FAMILIA', 'VDA_CALLE', 'VDA_NUMERODIRECCION', 'VDA_TIPOLOGIA']].drop_duplicates()

        for _, row in viviendas_unicas.iterrows():
            if pd.notna(row['PYTO_COD']) and pd.notna(row['VDA_CODIGO']):
                # Buscar el proyecto por codigo pero solo obtener el id para evitar cargar campos Decimal
                codigo_proyecto = f"{int(row['PYTO_COD'])}-{row['PYTO_SIGLAS']}"
                proyecto_id = Proyecto.objects.filter(codigo=codigo_proyecto).values_list('id', flat=True).first()

                if not proyecto_id:
                    self.stdout.write(f'Proyecto no encontrado: {codigo_proyecto}')
                    continue

                tipologia = Tipologia.objects.get(codigo=str(int(row['VDA_TIPOLOGIA']))) if pd.notna(row['VDA_TIPOLOGIA']) else None

                direccion = ""
                if pd.notna(row['VDA_CALLE']):
                    direccion = str(row['VDA_CALLE'])
                if pd.notna(row['VDA_NUMERODIRECCION']):
                    direccion += f" {row['VDA_NUMERODIRECCION']}"

                vivienda_exists = Vivienda.objects.filter(codigo=str(int(row['VDA_CODIGO'])), proyecto_id=proyecto_id).exists()
                if not vivienda_exists:
                    if dry_run:
                        self.stdout.write(f'[dry-run] Vivienda que se crearía: {str(int(row["VDA_CODIGO"]))} en proyecto {codigo_proyecto}')
                    else:
                        vivienda = Vivienda.objects.create(
                            codigo=str(int(row['VDA_CODIGO'])),
                            proyecto_id=proyecto_id,
                            familia_beneficiaria=row['VDA_FAMILIA'] or 'Sin especificar',
                            tipologia=tipologia,
                            estado='construccion'
                        )
                        self.stdout.write(f'Vivienda creada: {vivienda.codigo}')

    def importar_recintos(self, df, dry_run=False):
        """Importar recintos únicos del Excel"""
        self.stdout.write('Importando recintos...')

        # Obtener recintos únicos
        recintos_unicos = df[['RECINTO_COD', 'RECINTO_NOMBRE', 'RECINTO_TIPOLOGIA', 'RECINTO_ELEMENTOS']].drop_duplicates()

        for _, row in recintos_unicos.iterrows():
            if pd.notna(row['RECINTO_COD']) and pd.notna(row['RECINTO_NOMBRE']):
                try:
                    tipologia = Tipologia.objects.get(codigo=str(int(row['RECINTO_TIPOLOGIA']))) if pd.notna(row['RECINTO_TIPOLOGIA']) else None

                    # Normalizar elementos: Excel puede contener una cadena separada por comas
                    elementos_raw = row['RECINTO_ELEMENTOS'] if pd.notna(row.get('RECINTO_ELEMENTOS', None)) else ''
                    if isinstance(elementos_raw, (int, float)):
                        elementos_raw = str(elementos_raw)
                    elementos_list = [e.strip() for e in str(elementos_raw).split(',') if e.strip()] if elementos_raw else []

                    # El modelo Recinto usa 'elementos_disponibles' (JSONField)
                    recinto_exists = Recinto.objects.filter(codigo=str(int(row['RECINTO_COD'])), tipologia=tipologia).exists()
                    if not recinto_exists:
                        if dry_run:
                            self.stdout.write(f'[dry-run] Recinto que se crearía: {row["RECINTO_NOMBRE"]} ({str(int(row["RECINTO_COD"]))})')
                        else:
                            recinto = Recinto.objects.create(
                                codigo=str(int(row['RECINTO_COD'])),
                                tipologia=tipologia,
                                nombre=row['RECINTO_NOMBRE'],
                                elementos_disponibles=elementos_list,
                                activo=True
                            )
                            self.stdout.write(f'Recinto creado: {recinto.nombre}')

                except Exception as e:
                    self.stdout.write(f'Error creando recinto: {e}')

    def importar_observaciones(self, df, dry_run=False):
        """Importar observaciones del Excel"""
        self.stdout.write('Importando observaciones...')

        # Obtener usuario por defecto
        # Obtener el usuario importador por email
        try:
            usuario = User.objects.get(email='import@techo.org')
        except User.DoesNotExist:
            usuario = User.objects.create(email='import@techo.org', nombre='Importador Techo')

        # Estados por defecto
        estado_abierta = EstadoObservacion.objects.get(nombre='Abierta')
        estado_cerrada = EstadoObservacion.objects.get(nombre='Cerrada')
        estado_rechazada = EstadoObservacion.objects.get(nombre='Rechazada')

        # Tipo por defecto
        tipo_general = TipoObservacion.objects.get(nombre='General')

        observaciones_creadas = 0

        for _, row in df.iterrows():
            if pd.notna(row['PV_ID']) and pd.notna(row['PYTO_COD']) and pd.notna(row['VDA_CODIGO']):
                try:
                    # Buscar proyecto y vivienda por proyecto_id para evitar cargar campos Decimal
                    codigo_proyecto = f"{int(row['PYTO_COD'])}-{row['PYTO_SIGLAS']}"
                    proyecto_id = Proyecto.objects.filter(codigo=codigo_proyecto).values_list('id', flat=True).first()
                    if not proyecto_id:
                        self.stdout.write(f'Proyecto no encontrado: {codigo_proyecto}')
                        continue
                    vivienda = Vivienda.objects.get(codigo=str(int(row['VDA_CODIGO'])), proyecto_id=proyecto_id)

                    # Buscar recinto si existe
                    recinto = None
                    if pd.notna(row['RECINTO_COD']):
                        try:
                            recinto = Recinto.objects.get(codigo=str(int(row['RECINTO_COD'])))
                        except Recinto.DoesNotExist:
                            pass

                    # Mapear estado
                    estado = estado_abierta  # Por defecto
                    if pd.notna(row['PV_ESTADO']):
                        if int(row['PV_ESTADO']) == 1:
                            estado = estado_cerrada
                        elif int(row['PV_ESTADO']) == 99:
                            estado = estado_rechazada

                    # Parsear fecha
                    fecha_creacion = None
                    if pd.notna(row['PV_FECHAREGISTRO']):
                        try:
                            fecha_creacion = parse_datetime(str(row['PV_FECHAREGISTRO']))
                        except:
                            fecha_creacion = datetime.now()

                    # Determinar tipo de observación basado en elemento
                    tipo = tipo_general
                    elemento = str(row['PV_ELEMENTO']) if pd.notna(row['PV_ELEMENTO']) else ''

                    if any(x in elemento.lower() for x in ['puerta', 'ventana']):
                        tipo, _ = TipoObservacion.objects.get_or_create(nombre='Carpintería')
                    elif any(x in elemento.lower() for x in ['wc', 'tina', 'lavamanos']):
                        tipo, _ = TipoObservacion.objects.get_or_create(nombre='Sanitario')
                    elif any(x in elemento.lower() for x in ['luz', 'enchufe']):
                        tipo, _ = TipoObservacion.objects.get_or_create(nombre='Instalaciones')
                    elif any(x in elemento.lower() for x in ['pintura', 'piso', 'cielo']):
                        tipo, _ = TipoObservacion.objects.get_or_create(nombre='Terminaciones')

                    # Crear observación (verificar existencia por id_externo)
                    id_externo = str(int(row['PV_ID']))
                    existe = Observacion.objects.filter(id_externo=id_externo).exists()
                    if not existe:
                        if dry_run:
                            observaciones_creadas += 1
                            if observaciones_creadas % 100 == 0:
                                self.stdout.write(f'[dry-run] Observaciones que se crearían: {observaciones_creadas}')
                        else:
                            observacion = Observacion.objects.create(
                                id_externo=id_externo,
                                proyecto_id=proyecto_id,
                                vivienda=vivienda,
                                recinto=recinto,
                                elemento=elemento[:100],  # Limitar longitud
                                detalle=str(row['PV_DESCRIPCION']) if pd.notna(row['PV_DESCRIPCION']) else '',
                                tipo=tipo,
                                estado=estado,
                                es_urgente=row['PV_ESURGENTE'] == 1.0 if pd.notna(row['PV_ESURGENTE']) else False,
                                fecha_creacion=fecha_creacion or datetime.now(),
                                creado_por=usuario,
                                prioridad='alta' if row['PV_ESURGENTE'] == 1.0 else 'media'
                            )
                            observaciones_creadas += 1
                            if observaciones_creadas % 100 == 0:
                                self.stdout.write(f'Observaciones creadas: {observaciones_creadas}')

                except Exception as e:
                    self.stdout.write(f'Error creando observación {row["PV_ID"]}: {e}')

        self.stdout.write(f'Total observaciones creadas: {observaciones_creadas}')

    def obtener_usuario_email(self, email):
        """Obtener o crear usuario por email"""
        if pd.notna(email):
            # Crear o obtener usuario usando email como identificador
            user, _ = User.objects.get_or_create(
                email=email,
                defaults={'nombre': email.split('@')[0]}
            )
            return user
        try:
            return User.objects.get(email='import@techo.org')
        except User.DoesNotExist:
            return User.objects.create(email='import@techo.org', nombre='Importador Techo')
