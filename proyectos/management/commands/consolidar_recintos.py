from django.core.management.base import BaseCommand
from proyectos.models import Recinto, TipologiaVivienda
from django.db.models import Count

class Command(BaseCommand):
    help = 'Consolida recintos duplicados por nombre, unificando sus elementos disponibles'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Iniciando consolidación de recintos...'))
        
        # Obtener todas las tipologías
        tipologias = TipologiaVivienda.objects.all()
        
        recintos_consolidados = 0
        recintos_eliminados = 0
        
        for tipologia in tipologias:
            self.stdout.write(f'\n📋 Procesando tipología: {tipologia.nombre}')
            
            # Obtener todos los recintos de esta tipología
            recintos = Recinto.objects.filter(tipologia=tipologia)
            
            # Agrupar por nombre
            nombres_recintos = recintos.values('nombre').annotate(
                total=Count('id')
            ).order_by('nombre')
            
            for item in nombres_recintos:
                nombre = item['nombre']
                total = item['total']
                
                if total > 1:
                    self.stdout.write(f'  🔄 Encontrados {total} recintos con nombre "{nombre}"')
                    
                    # Obtener todos los recintos con este nombre
                    recintos_duplicados = Recinto.objects.filter(
                        tipologia=tipologia,
                        nombre=nombre
                    ).order_by('id')
                    
                    # El primero será el que mantengamos
                    recinto_principal = recintos_duplicados.first()
                    elementos_unificados = set(recinto_principal.elementos_disponibles or [])
                    
                    self.stdout.write(f'    ✓ Recinto principal ID: {recinto_principal.id}')
                    self.stdout.write(f'    ✓ Elementos iniciales: {len(elementos_unificados)}')
                    
                    # Agregar elementos de los demás recintos
                    for recinto_duplicado in recintos_duplicados[1:]:
                        if recinto_duplicado.elementos_disponibles:
                            nuevos_elementos = set(recinto_duplicado.elementos_disponibles)
                            elementos_antes = len(elementos_unificados)
                            elementos_unificados.update(nuevos_elementos)
                            elementos_agregados = len(elementos_unificados) - elementos_antes
                            
                            self.stdout.write(
                                f'    + ID {recinto_duplicado.id}: {elementos_agregados} elementos nuevos'
                            )
                        
                        # Eliminar el recinto duplicado
                        recinto_duplicado.delete()
                        recintos_eliminados += 1
                    
                    # Actualizar el recinto principal con todos los elementos
                    elementos_lista = sorted(list(elementos_unificados))
                    recinto_principal.elementos_disponibles = elementos_lista
                    recinto_principal.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'    ✅ Consolidado "{nombre}": {len(elementos_lista)} elementos totales'
                        )
                    )
                    recintos_consolidados += 1
                else:
                    # Solo hay uno, verificar que tenga elementos
                    recinto_unico = recintos.get(nombre=nombre)
                    if recinto_unico.elementos_disponibles:
                        # Eliminar duplicados dentro del mismo recinto
                        elementos_originales = recinto_unico.elementos_disponibles
                        elementos_unicos = sorted(list(set(elementos_originales)))
                        
                        if len(elementos_unicos) < len(elementos_originales):
                            recinto_unico.elementos_disponibles = elementos_unicos
                            recinto_unico.save()
                            self.stdout.write(
                                f'  🔧 Limpiado "{nombre}": {len(elementos_originales)} → {len(elementos_unicos)} elementos'
                            )
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Consolidación completada!'
            )
        )
        self.stdout.write(f'   📊 Recintos consolidados: {recintos_consolidados}')
        self.stdout.write(f'   🗑️  Recintos eliminados: {recintos_eliminados}')
        self.stdout.write('\n' + '='*60)
        
        # Mostrar resumen de recintos actuales
        self.stdout.write('\n📋 RESUMEN DE RECINTOS ACTUALES:\n')
        
        for tipologia in tipologias:
            recintos = Recinto.objects.filter(tipologia=tipologia).order_by('nombre')
            if recintos.exists():
                self.stdout.write(f'\n🏠 {tipologia.nombre}:')
                for recinto in recintos:
                    total_elementos = len(recinto.elementos_disponibles or [])
                    self.stdout.write(f'   • {recinto.nombre}: {total_elementos} elementos')
                    if total_elementos > 0 and total_elementos <= 10:
                        for elemento in recinto.elementos_disponibles:
                            self.stdout.write(f'     - {elemento}')
                    elif total_elementos > 10:
                        for elemento in recinto.elementos_disponibles[:5]:
                            self.stdout.write(f'     - {elemento}')
                        self.stdout.write(f'     ... y {total_elementos - 5} más')
