from django.core.management.base import BaseCommand
from proyectos.models import Beneficiario, Vivienda, Proyecto
from core.models import Usuario


class Command(BaseCommand):
    help = 'Crea un nuevo beneficiario para probar el signal de creación automática de usuario'

    def handle(self, *args, **kwargs):
        rut_nuevo = '98765432-1'
        email_nuevo = 'maria.gonzalez@beneficiario.cl'
        
        self.stdout.write('=== PRUEBA DE CREACIÓN AUTOMÁTICA DE USUARIO ===\n')
        
        # Verificar si ya existe
        if Beneficiario.objects.filter(rut=rut_nuevo).exists():
            self.stdout.write(self.style.WARNING(f'Ya existe un beneficiario con RUT {rut_nuevo}'))
            self.stdout.write('Eliminando para volver a probar...')
            Beneficiario.objects.filter(rut=rut_nuevo).delete()
            Usuario.objects.filter(rut=rut_nuevo).delete()
        
        self.stdout.write('\n1️⃣ Creando beneficiario...')
        beneficiario = Beneficiario.objects.create(
            nombre='María',
            apellido_paterno='González',
            apellido_materno='López',
            rut=rut_nuevo,
            email=email_nuevo
        )
        self.stdout.write(self.style.SUCCESS(f'   ✓ Beneficiario creado: {beneficiario}'))
        self.stdout.write(f'     RUT: {rut_nuevo}')
        self.stdout.write(f'     Email: {email_nuevo}')
        
        # Esperar un momento para que el signal se ejecute
        import time
        time.sleep(0.5)
        
        # Verificar si el usuario se creó automáticamente
        self.stdout.write('\n2️⃣ Verificando creación automática de usuario FAMILIA...')
        try:
            usuario = Usuario.objects.get(rut=rut_nuevo)
            self.stdout.write(self.style.SUCCESS(f'   ✓ ¡Usuario creado automáticamente por el signal!'))
            self.stdout.write(f'     Email: {usuario.email}')
            self.stdout.write(f'     Nombre: {usuario.nombre}')
            self.stdout.write(f'     RUT: {usuario.rut}')
            self.stdout.write(f'     Rol: {usuario.rol.nombre if usuario.rol else "Sin rol"}')
            self.stdout.write(f'     Contraseña: familia123')
            
        except Usuario.DoesNotExist:
            self.stdout.write(self.style.ERROR('   ✗ No se creó el usuario automáticamente'))
            self.stdout.write('   Verifica que el signal esté registrado correctamente')
            return
        
        # Asignar una vivienda
        self.stdout.write('\n3️⃣ Asignando vivienda al beneficiario...')
        proyecto = Proyecto.objects.first()
        if proyecto:
            tipologia = proyecto.viviendas.first().tipologia if proyecto.viviendas.exists() else None
            
            # Generar código único
            import random
            codigo_vivienda = f'V-TEST-{random.randint(1000, 9999)}'
            
            vivienda = Vivienda.objects.create(
                proyecto=proyecto,
                tipologia=tipologia,
                codigo=codigo_vivienda,
                familia_beneficiaria=f'{beneficiario.nombre} {beneficiario.apellido_paterno}',
                beneficiario=beneficiario,
                estado='entregada'
            )
            self.stdout.write(self.style.SUCCESS(f'   ✓ Vivienda creada: {vivienda}'))
            codigo_final = codigo_vivienda
        else:
            self.stdout.write(self.style.WARNING('   ⚠ No hay proyectos disponibles'))
            codigo_final = 'N/A'
        
        # Resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✅ PRUEBA EXITOSA - SIGNAL FUNCIONANDO'))
        self.stdout.write('='*60)
        self.stdout.write('\n📋 DATOS PARA LOGIN:')
        self.stdout.write(f'   URL: http://127.0.0.1:8000/login/')
        self.stdout.write(f'   Usuario: {email_nuevo}')
        self.stdout.write(f'   Contraseña: familia123')
        self.stdout.write('\n🏠 VIVIENDA ASIGNADA:')
        if proyecto:
            self.stdout.write(f'   Proyecto: {proyecto.nombre}')
            self.stdout.write(f'   Vivienda: {codigo_final}')
        self.stdout.write('\n📝 QUÉ PROBAR:')
        self.stdout.write('   1. Login con las credenciales de arriba')
        self.stdout.write('   2. Verificar que el dashboard muestre su vivienda')
        self.stdout.write('   3. Ir a "Mis Observaciones"')
        self.stdout.write('   4. Crear una nueva observación (debe cargar automáticamente su vivienda)')
        self.stdout.write('')
