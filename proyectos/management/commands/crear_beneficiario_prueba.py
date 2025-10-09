from django.core.management.base import BaseCommand
from proyectos.models import Beneficiario, Vivienda, Proyecto
from core.models import Usuario


class Command(BaseCommand):
    help = 'Crea un beneficiario de prueba con RUT 12345678-9 y asigna una vivienda'

    def handle(self, *args, **kwargs):
        rut_prueba = '12345678-9'
        email_prueba = 'familia@beneficiario.cl'
        
        # Verificar si ya existe
        if Beneficiario.objects.filter(rut=rut_prueba).exists():
            self.stdout.write(self.style.WARNING(f'Ya existe un beneficiario con RUT {rut_prueba}'))
            beneficiario = Beneficiario.objects.get(rut=rut_prueba)
        else:
            # Crear beneficiario
            beneficiario = Beneficiario.objects.create(
                nombre='Juan',
                apellido_paterno='Pérez',
                apellido_materno='González',
                rut=rut_prueba,
                email=email_prueba
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Beneficiario creado: {beneficiario}'))
            self.stdout.write(f'  RUT: {rut_prueba}')
            self.stdout.write(f'  Email: {email_prueba}')
        
        # Verificar si el usuario se creó automáticamente (por el signal)
        try:
            usuario = Usuario.objects.get(rut=rut_prueba)
            self.stdout.write(self.style.SUCCESS(f'✓ Usuario FAMILIA automático: {usuario.email}'))
            self.stdout.write(f'  Login con: {usuario.email} / familia123')
        except Usuario.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠ No se creó usuario automáticamente. Verifica los signals.'))
        
        # Buscar un proyecto existente para asignar vivienda
        proyecto = Proyecto.objects.first()
        if proyecto:
            # Buscar si ya tiene vivienda asignada
            vivienda_existente = Vivienda.objects.filter(beneficiario=beneficiario).first()
            
            if vivienda_existente:
                self.stdout.write(self.style.SUCCESS(f'✓ Ya tiene vivienda: {vivienda_existente}'))
            else:
                # Crear una vivienda de prueba
                vivienda = Vivienda.objects.create(
                    proyecto=proyecto,
                    tipologia=proyecto.viviendas.first().tipologia if proyecto.viviendas.exists() else None,
                    codigo='V-PRUEBA-001',
                    familia_beneficiaria=f'{beneficiario.nombre} {beneficiario.apellido_paterno}',
                    beneficiario=beneficiario,
                    estado='entregada'
                )
                self.stdout.write(self.style.SUCCESS(f'✓ Vivienda creada: {vivienda}'))
        else:
            self.stdout.write(self.style.WARNING('⚠ No hay proyectos. No se pudo crear vivienda.'))
        
        self.stdout.write(self.style.SUCCESS('\n=== RESUMEN ==='))
        self.stdout.write(f'Beneficiario: {beneficiario}')
        self.stdout.write(f'RUT: {rut_prueba}')
        self.stdout.write(f'Email: {email_prueba}')
        self.stdout.write(f'\nPara hacer login:')
        self.stdout.write(f'  Usuario: {email_prueba}')
        self.stdout.write(f'  Contraseña: familia123')
