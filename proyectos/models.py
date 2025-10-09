
from django.db import models
from core.validators import validar_rut
from django.conf import settings
from datetime import timedelta, datetime
from core.models import Region, Comuna
from django.db.models.signals import post_save
from django.dispatch import receiver

class TipologiaVivienda(models.Model):
    id = models.AutoField(primary_key=True)
    codigo = models.IntegerField(unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    class Meta:
        verbose_name = "Tipología de Vivienda"
        verbose_name_plural = "Tipologías de Vivienda"
        ordering = ['codigo']

class Proyecto(models.Model):
    id = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True, help_text="Código único del proyecto (ej: LC1, COP8)")
    siglas = models.CharField(max_length=10, help_text="Siglas del proyecto")
    nombre = models.CharField(max_length=200, verbose_name="Nombre del proyecto")

    constructora = models.CharField(max_length=100)
    comuna = models.ForeignKey(Comuna, on_delete=models.PROTECT)
    region = models.ForeignKey(Region, on_delete=models.PROTECT)

    fecha_entrega = models.DateField(help_text="Fecha de entrega de las viviendas")
    fecha_termino_postventa = models.DateField(blank=True, null=True, 
                                              help_text="120 días después de la entrega según DS49")

    coordenadas_s = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True,
                                       verbose_name="Latitud (S)")
    coordenadas_w = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True,
                                       verbose_name="Longitud (W)")

    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                   related_name='proyectos_creados')

    def save(self, *args, **kwargs):
        if self.fecha_entrega and not self.fecha_termino_postventa:
            self.fecha_termino_postventa = self.fecha_entrega + timedelta(days=120)
        super().save(*args, **kwargs)

    @property
    def dias_restantes_postventa(self):
        if self.fecha_termino_postventa:
            delta = self.fecha_termino_postventa - datetime.now().date()
            return max(0, delta.days)
        return 0

    @property
    def estado_postventa(self):
        if not self.fecha_termino_postventa:
            return "Sin definir"
        dias_restantes = self.dias_restantes_postventa
        if dias_restantes > 30:
            return "Vigente"
        elif dias_restantes > 0:
            return "Por vencer"
        else:
            return "Vencido"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    class Meta:
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"
        ordering = ['-fecha_creacion']

class Recinto(models.Model):
    id = models.AutoField(primary_key=True)
    tipologia = models.ForeignKey(TipologiaVivienda, on_delete=models.CASCADE,
                                 related_name='recintos')
    codigo = models.CharField(max_length=10)
    nombre = models.CharField(max_length=100, help_text="Ej: Estar-comedor, Cocina, Dormitorio 1")
    descripcion = models.TextField(blank=True)

    elementos_disponibles = models.JSONField(
        default=list,
        help_text="Lista de elementos que pueden tener observaciones en este recinto"
    )

    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.tipologia.codigo} - {self.nombre}"

    class Meta:
        verbose_name = "Recinto"
        verbose_name_plural = "Recintos"
        unique_together = ('tipologia', 'codigo')
        ordering = ['tipologia__codigo', 'codigo']


class Beneficiario(models.Model):
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100, verbose_name="Apellido Paterno", default="")
    apellido_materno = models.CharField(max_length=100, verbose_name="Apellido Materno", blank=True, null=True)
    rut = models.CharField(max_length=12, unique=True, validators=[validar_rut], blank=True, null=True)
    email = models.EmailField(max_length=254, blank=True, null=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno or ''}".strip()

    class Meta:
        verbose_name = "Beneficiario"
        verbose_name_plural = "Beneficiarios"
        ordering = ['apellido_paterno', 'apellido_materno', 'nombre']

class Telefono(models.Model):
    beneficiario = models.ForeignKey(Beneficiario, on_delete=models.CASCADE, related_name='telefonos')
    numero = models.CharField(max_length=20, verbose_name="Teléfono")
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.numero

    class Meta:
        verbose_name = "Teléfono"
        verbose_name_plural = "Teléfonos"

class Vivienda(models.Model):
    ESTADOS_CHOICES = [
        ('construccion', 'En Construcción'),
        ('entregada', 'Entregada'),
        ('postventa', 'En Postventa'),
        ('terminada', 'Terminada'),
    ]

    id = models.AutoField(primary_key=True)
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='viviendas')
    tipologia = models.ForeignKey(TipologiaVivienda, on_delete=models.PROTECT)

    codigo = models.CharField(max_length=10, help_text="Código único de la vivienda dentro del proyecto")
    familia_beneficiaria = models.CharField(max_length=200, help_text="Nombre de la familia")
    beneficiario = models.ForeignKey(Beneficiario, null=True, blank=True, on_delete=models.SET_NULL, related_name='viviendas')
    estado = models.CharField(max_length=20, choices=ESTADOS_CHOICES, default='construccion')

    fecha_entrega = models.DateField(blank=True, null=True)
    fecha_inicio_postventa = models.DateField(blank=True, null=True)
    fecha_termino_postventa = models.DateField(blank=True, null=True)

    observaciones_generales = models.TextField(blank=True)
    activa = models.BooleanField(default=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.proyecto.codigo} - Vivienda {self.codigo}"

    class Meta:
        verbose_name = "Vivienda"
        verbose_name_plural = "Viviendas"
        unique_together = ('proyecto', 'codigo')
        ordering = ['proyecto', 'codigo']


# ============================================
# SIGNALS - Creación automática de usuarios
# ============================================

@receiver(post_save, sender=Beneficiario)
def crear_usuario_familia(sender, instance, created, **kwargs):
    """
    Signal que automáticamente crea un usuario FAMILIA cuando se crea un Beneficiario.
    
    - Username: RUT del beneficiario
    - Email: Email del beneficiario
    - Password: 'familia123' (por defecto)
    - Rol: FAMILIA
    - Nombre: Nombre completo del beneficiario
    """
    if created and instance.rut and instance.email:
        # Importar aquí para evitar circular imports
        from core.models import Usuario, Rol
        
        # Verificar si ya existe un usuario con ese RUT
        if not Usuario.objects.filter(rut=instance.rut).exists():
            try:
                # Obtener el rol FAMILIA
                rol_familia = Rol.objects.get(nombre='FAMILIA')
                
                # Crear el usuario
                nombre_completo = f"{instance.nombre} {instance.apellido_paterno} {instance.apellido_materno or ''}".strip()
                
                usuario = Usuario.objects.create_user(
                    email=instance.email,
                    password='familia123',  # Contraseña por defecto
                    nombre=nombre_completo,
                    rut=instance.rut,
                    rol=rol_familia
                )
                
                print(f"✓ Usuario FAMILIA creado automáticamente: {usuario.email} (RUT: {instance.rut})")
                print(f"  Contraseña temporal: familia123")
                
            except Rol.DoesNotExist:
                print(f"⚠ Error: No existe el rol FAMILIA. No se pudo crear usuario para {instance.rut}")
            except Exception as e:
                print(f"⚠ Error al crear usuario para beneficiario {instance.rut}: {str(e)}")
        else:
            print(f"ℹ Ya existe un usuario con RUT {instance.rut}, no se creó uno nuevo")
