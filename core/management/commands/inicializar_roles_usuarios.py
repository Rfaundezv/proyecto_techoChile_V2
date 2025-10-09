"""
Management command para inicializar roles y usuarios de demostración
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Usuario, Rol

class Command(BaseCommand):
    help = 'Inicializa roles y crea usuarios de demostración para cada rol'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== Inicializando Roles y Usuarios ===\n'))

        with transaction.atomic():
            # 1. Crear/Actualizar Roles
            self.stdout.write('1. Creando/actualizando roles...')
            
            roles_data = [
                {
                    'nombre': 'ADMINISTRADOR',
                    'descripcion': 'Acceso completo al sistema, gestión de usuarios y configuración'
                },
                {
                    'nombre': 'TECHO',
                    'descripcion': 'Personal de TECHO Chile - Acceso total + reportes + gestión de proyectos'
                },
                {
                    'nombre': 'SERVIU',
                    'descripcion': 'SERVIU - Acceso de solo lectura + descarga de reportes'
                },
                {
                    'nombre': 'CONSTRUCTORA',
                    'descripcion': 'Empresa Constructora - Ver observaciones asignadas + subir evidencias'
                },
                {
                    'nombre': 'FAMILIA',
                    'descripcion': 'Familia Beneficiaria - Crear y ver sus propias observaciones'
                },
            ]

            for rol_data in roles_data:
                rol, created = Rol.objects.update_or_create(
                    nombre=rol_data['nombre'],
                    defaults={
                        'descripcion': rol_data['descripcion'],
                        'activo': True
                    }
                )
                action = 'Creado' if created else 'Actualizado'
                self.stdout.write(f'   ✓ {action}: {rol.get_nombre_display()}')

            # 2. Crear Usuarios de Demostración
            self.stdout.write('\n2. Creando usuarios de demostración...')
            
            usuarios_demo = [
                {
                    'email': 'admin@techo.cl',
                    'password': 'admin123',
                    'nombre': 'Administrador Sistema',
                    'rol_nombre': 'ADMINISTRADOR',
                    'is_staff': True,
                    'is_superuser': True,
                },
                {
                    'email': 'techo@techo.cl',
                    'password': 'techo123',
                    'nombre': 'Personal TECHO',
                    'rol_nombre': 'TECHO',
                    'is_staff': True,
                    'is_superuser': False,
                },
                {
                    'email': 'serviu@gobierno.cl',
                    'password': 'serviu123',
                    'nombre': 'Inspector SERVIU',
                    'rol_nombre': 'SERVIU',
                    'is_staff': False,
                    'is_superuser': False,
                },
                {
                    'email': 'constructora@empresa.cl',
                    'password': 'const123',
                    'nombre': 'Representante Constructora',
                    'rol_nombre': 'CONSTRUCTORA',
                    'empresa': 'Constructora Ejemplo S.A.',
                    'is_staff': False,
                    'is_superuser': False,
                },
                {
                    'email': 'familia@beneficiario.cl',
                    'password': 'familia123',
                    'nombre': 'Juan Pérez Familia',
                    'rut': '12345678-9',  # RUT de ejemplo para hacer match con beneficiario
                    'rol_nombre': 'FAMILIA',
                    'is_staff': False,
                    'is_superuser': False,
                },
            ]

            for user_data in usuarios_demo:
                rol = Rol.objects.get(nombre=user_data.pop('rol_nombre'))
                email = user_data.pop('email')
                password = user_data.pop('password')
                
                # Verificar si el usuario ya existe
                try:
                    usuario = Usuario.objects.get(email=email)
                    # Actualizar datos
                    for key, value in user_data.items():
                        setattr(usuario, key, value)
                    usuario.rol = rol
                    usuario.set_password(password)
                    usuario.save()
                    self.stdout.write(f'   ✓ Actualizado: {usuario.email} ({rol.get_nombre_display()})')
                except Usuario.DoesNotExist:
                    # Crear nuevo usuario
                    usuario = Usuario.objects.create_user(
                        email=email,
                        password=password,
                        **user_data
                    )
                    usuario.rol = rol
                    usuario.save()
                    self.stdout.write(f'   ✓ Creado: {usuario.email} ({rol.get_nombre_display()})')

            # 3. Mostrar resumen
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('\n✓ Inicialización completada exitosamente!\n'))
            self.stdout.write('='*60)
            
            self.stdout.write('\n📊 RESUMEN DE USUARIOS CREADOS:\n')
            self.stdout.write('-' * 60)
            self.stdout.write(f'{"Email":<30} {"Rol":<20} {"Password"}')
            self.stdout.write('-' * 60)
            
            usuarios_list = [
                ('admin@techo.cl', 'ADMINISTRADOR', 'admin123'),
                ('techo@techo.cl', 'TECHO', 'techo123'),
                ('serviu@gobierno.cl', 'SERVIU', 'serviu123'),
                ('constructora@empresa.cl', 'CONSTRUCTORA', 'const123'),
                ('familia@beneficiario.cl', 'FAMILIA', 'familia123'),
            ]
            
            for email, rol, password in usuarios_list:
                self.stdout.write(f'{email:<30} {rol:<20} {password}')
            
            self.stdout.write('-' * 60)
            self.stdout.write(f'\n📈 Total de usuarios activos: {Usuario.objects.filter(is_active=True).count()}')
            self.stdout.write(f'📋 Total de roles configurados: {Rol.objects.filter(activo=True).count()}\n')
            
            # 4. Instrucciones
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.WARNING('\n⚠️  INSTRUCCIONES IMPORTANTES:\n'))
            self.stdout.write('='*60)
            self.stdout.write('''
1. Estos son usuarios de DEMOSTRACIÓN con contraseñas simples
2. En producción, cambia todas las contraseñas por seguras
3. Puedes iniciar sesión con cualquiera de los usuarios listados
4. Cada usuario tiene permisos específicos según su rol
5. Para crear más usuarios, usa el admin de Django o crea un formulario

📚 Documentación completa en: CONTROL_ACCESO_ROLES.md
''')
            self.stdout.write('='*60 + '\n')
