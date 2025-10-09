from django.core.management.base import BaseCommand
from core.models import Usuario


class Command(BaseCommand):
    help = 'Actualiza el usuario FAMILIA existente con el RUT del beneficiario'

    def handle(self, *args, **kwargs):
        rut_prueba = '12345678-9'
        email_familia = 'familia@beneficiario.cl'
        
        try:
            usuario = Usuario.objects.get(email=email_familia)
            
            if usuario.rut:
                self.stdout.write(self.style.WARNING(f'El usuario ya tiene RUT: {usuario.rut}'))
            else:
                usuario.rut = rut_prueba
                usuario.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Usuario actualizado con RUT: {rut_prueba}'))
                self.stdout.write(f'  Email: {usuario.email}')
                self.stdout.write(f'  Nombre: {usuario.nombre}')
                self.stdout.write(f'  Rol: {usuario.rol.nombre if usuario.rol else "Sin rol"}')
                
        except Usuario.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'No existe usuario con email {email_familia}'))
        
        self.stdout.write(self.style.SUCCESS('\nAhora el usuario FAMILIA está vinculado por RUT con el beneficiario'))
