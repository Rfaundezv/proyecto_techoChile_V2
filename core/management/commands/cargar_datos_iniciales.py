
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Rol, Region, Comuna, Constructora

User = get_user_model()

class Command(BaseCommand):
    help = 'Carga datos iniciales del sistema'

    def handle(self, *args, **kwargs):
        # Crear roles
        roles = ['SERVIU', 'CONSTRUCTORA', 'TECHO', 'ADMINISTRADOR']
        for rol_nombre in roles:
            rol, created = Rol.objects.get_or_create(nombre=rol_nombre)
            if created:
                self.stdout.write(f'Creado rol: {rol_nombre}')

        # Crear usuario administrador
        if not User.objects.filter(email='admin@techo.cl').exists():
            admin_rol = Rol.objects.get(nombre='ADMINISTRADOR')
            admin_user = User.objects.create_user(
                email='admin@techo.cl',
                password='admin123',
                nombre='Administrador Sistema',
                rol=admin_rol,
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write('Creado usuario administrador: admin@techo.cl / admin123')

        # Crear algunas constructoras
        rm_region = Region.objects.filter(codigo='RM').first()
        if rm_region:
            constructoras = [
                {'nombre': 'Constructora ABC', 'region': rm_region},
                {'nombre': 'Inmobiliaria XYZ', 'region': rm_region},
                {'nombre': 'Constructora Los Andes', 'region': rm_region},
            ]

            for const_data in constructoras:
                const, created = Constructora.objects.get_or_create(
                    nombre=const_data['nombre'],
                    defaults=const_data
                )
                if created:
                    self.stdout.write(f'Creada constructora: {const.nombre}')

        self.stdout.write(self.style.SUCCESS('Datos iniciales cargados correctamente'))
