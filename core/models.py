
from django.db import models
from .validators import validar_rut
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager, Group, Permission
from datetime import timedelta, datetime

class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)

class Rol(models.Model):
    id = models.AutoField(primary_key=True)
    ROLES_CHOICES = (
        ('SERVIU', 'SERVIU'),
        ('CONSTRUCTORA', 'Empresa Constructora'),
        ('TECHO', 'TECHO Chile'),
        ('ADMINISTRADOR', 'Administrador Sistema'),
        ('FAMILIA', 'Familia Beneficiaria'),
    )
    nombre = models.CharField(max_length=50, choices=ROLES_CHOICES, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.get_nombre_display()

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"

class Region(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=10, unique=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Región"
        verbose_name_plural = "Regiones"
        ordering = ['codigo']

class Comuna(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name='comunas')
    codigo = models.CharField(max_length=10, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ('nombre', 'region')
        verbose_name = "Comuna"
        verbose_name_plural = "Comunas"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre}, {self.region.nombre}"

class Usuario(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True, verbose_name="Correo electrónico")
    rut = models.CharField(
        max_length=12, 
        unique=True, 
        null=True, 
        blank=True,
        verbose_name="RUT",
        help_text="RUT del usuario (para familias beneficiarias). Ej: 12345678-9",
        validators=[validar_rut],
        db_index=True
    )
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido_paterno = models.CharField(max_length=100, verbose_name="Apellido paterno", blank=True, null=True)
    apellido_materno = models.CharField(max_length=100, verbose_name="Apellido materno", blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, verbose_name="Teléfono")
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, null=True, blank=True)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    comuna = models.ForeignKey(Comuna, on_delete=models.SET_NULL, null=True, blank=True)
    constructora = models.ForeignKey('Constructora', on_delete=models.SET_NULL, null=True, blank=True, help_text="Constructora asociada (solo para usuarios con rol Constructora)")
    empresa = models.CharField(max_length=200, blank=True, help_text="Para usuarios de constructoras (campo legacy, usar constructora)")  # Mantener por compatibilidad

    is_active = models.BooleanField(default=True, verbose_name="Activo")
    is_staff = models.BooleanField(default=False, verbose_name="Es staff")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de registro")

    groups = models.ManyToManyField(
        Group,
        related_name='usuarios_custom',
        blank=True,
        help_text='Grupos de usuario.',
        verbose_name='grupos'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='usuarios_custom',
        blank=True,
        help_text='Permisos de usuario.',
        verbose_name='permisos de usuario'
    )

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.email})"

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

class Constructora(models.Model):
    nombre = models.CharField(max_length=150, unique=True, verbose_name="Nombre Constructora")
    direccion = models.CharField(max_length=255, blank=True, verbose_name="Dirección")
    rut = models.CharField(max_length=15, blank=True, null=True, verbose_name="RUT", db_index=True, validators=[validar_rut])
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    comuna = models.ForeignKey(Comuna, on_delete=models.SET_NULL, null=True, blank=True)
    contacto = models.CharField(max_length=100, blank=True, verbose_name="Contacto")
    telefono = models.CharField(max_length=30, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Correo electrónico")
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Constructora"
        verbose_name_plural = "Constructoras"
        ordering = ['nombre']


class ConfiguracionObservacion(models.Model):
    """Configuración de tiempos por defecto para observaciones"""
    dias_vencimiento_normal = models.IntegerField(
        default=120,
        verbose_name="Días de vencimiento (Normal)",
        help_text="Días por defecto para observaciones normales"
    )
    horas_vencimiento_urgente = models.IntegerField(
        default=48,
        verbose_name="Horas de vencimiento (Urgente)",
        help_text="Horas por defecto para observaciones urgentes"
    )
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Última modificación")
    modificado_por = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Modificado por"
    )
    
    def __str__(self):
        return f"Configuración de Observaciones - Normal: {self.dias_vencimiento_normal} días, Urgente: {self.horas_vencimiento_urgente} horas"
    
    class Meta:
        verbose_name = "Configuración de Observación"
        verbose_name_plural = "Configuración de Observaciones"
    
    @classmethod
    def get_configuracion(cls):
        """Obtiene la configuración actual o crea una por defecto"""
        config = cls.objects.first()
        if not config:
            config = cls.objects.create()
        return config
