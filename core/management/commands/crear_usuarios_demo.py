from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from core.models import Rol

Usuario = get_user_model()

class Command(BaseCommand):
    help = 'Crear usuarios de demostración del sistema'

    def handle(self, *args, **options):
        usuarios_demo = [
            {
                'email': 'coordinador@techo.cl',
                'password': 'techo123',
                'nombre': 'María González Coordinadora',
                'rol_nombre': 'TECHO',
                'is_active': True
            },
            {
                'email': 'supervisor@constructora.cl',
                'password': 'const123',
                'nombre': 'Carlos Mendoza Supervisor',
                'rol_nombre': 'CONSTRUCTORA',
                'empresa': 'Constructora Ejemplo S.A.',
                'is_active': True
            },
            {
                'email': 'inspector@serviu.cl',
                'password': 'serviu123',
                'nombre': 'Ana Rodríguez Inspector SERVIU',
                'rol_nombre': 'SERVIU',
                'is_active': True
            }
        ]

        with transaction.atomic():
            for usuario_data in usuarios_demo:
                email = usuario_data['email']
                
                # Verificar si ya existe
                if Usuario.objects.filter(email=email).exists():
                    self.stdout.write(
                        self.style.WARNING(f'El usuario {email} ya existe, saltando...')
                    )
                    continue

                # Obtener el rol
                try:
                    rol = Rol.objects.get(nombre=usuario_data['rol_nombre'])
                except Rol.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Rol {usuario_data["rol_nombre"]} no existe')
                    )
                    continue

                # Crear usuario
                usuario_kwargs = {
                    'email': email,
                    'password': usuario_data['password'],
                    'nombre': usuario_data['nombre'],
                    'rol': rol,
                    'is_active': usuario_data['is_active']
                }
                
                # Agregar empresa si existe
                if 'empresa' in usuario_data:
                    usuario_kwargs['empresa'] = usuario_data['empresa']
                
                usuario = Usuario.objects.create_user(**usuario_kwargs)

                self.stdout.write(
                    self.style.SUCCESS(f'✅ Usuario creado: {email} (Rol: {rol.nombre})')
                )

        self.stdout.write(
            self.style.SUCCESS('\n🎉 ¡Usuarios de demostración creados exitosamente!')
        )
        self.stdout.write('📋 Usuarios disponibles en el sistema:')
        
        # Mostrar todos los usuarios
        for usuario in Usuario.objects.all().order_by('rol', 'email'):
            rol_display = usuario.rol.nombre if usuario.rol else 'Sin rol'
            self.stdout.write(f'  • {usuario.email} - {usuario.nombre} (Rol: {rol_display})')