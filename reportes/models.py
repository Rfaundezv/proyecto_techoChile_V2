
from django.db import models
from django.contrib.auth import get_user_model
import json

class ReporteGenerado(models.Model):
    usuario = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    nombre_archivo = models.CharField(max_length=255)
    ruta_archivo = models.CharField(max_length=255)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    filtros = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.nombre_archivo} ({self.fecha_generacion:%d/%m/%Y %H:%M})"

    class Meta:
        verbose_name = "Reporte generado"
        verbose_name_plural = "Reportes generados"
        ordering = ['-fecha_generacion']
from django.db import models
from django.conf import settings
from proyectos.models import Proyecto, Vivienda, Beneficiario
from core.models import Constructora


class ActaRecepcion(models.Model):
    """Modelo para las Actas de Recepción de Viviendas"""
    
    # Relaciones principales
    vivienda = models.OneToOneField(
        Vivienda, 
        on_delete=models.PROTECT, 
        related_name='acta_recepcion',
        verbose_name="Vivienda"
    )
    proyecto = models.ForeignKey(
        Proyecto, 
        on_delete=models.PROTECT,
        verbose_name="Proyecto"
    )
    beneficiario = models.ForeignKey(
        Beneficiario, 
        on_delete=models.PROTECT,
        verbose_name="Beneficiario"
    )
    
    # Información del acta
    numero_acta = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Número de Acta",
        help_text="Número único del acta (ej: ACT-2025-001)"
    )
    fecha_entrega = models.DateTimeField(verbose_name="Fecha y Hora de Entrega")
    lugar_entrega = models.CharField(
        max_length=200, 
        verbose_name="Lugar de Entrega",
        help_text="Dirección exacta donde se realiza la entrega"
    )
    
    # Representante de TECHO
    representante_techo = models.CharField(
        max_length=100, 
        verbose_name="Representante TECHO"
    )
    cargo_representante = models.CharField(
        max_length=100, 
        verbose_name="Cargo del Representante"
    )
    rut_representante = models.CharField(
        max_length=12, 
        verbose_name="RUT del Representante"
    )
    telefono_representante = models.CharField(
        max_length=20, 
        verbose_name="Teléfono del Representante"
    )
    
    # Información de construcción
    jefe_construccion = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Jefe de Construcción"
    )
    numero_voluntarios = models.PositiveIntegerField(
        default=0,
        verbose_name="Número de Voluntarios"
    )
    
    # Estado de la vivienda
    estado_estructura = models.BooleanField(
        default=True,
        verbose_name="Estado Estructura",
        help_text="True = Conforme, False = Con observaciones"
    )
    estado_instalaciones = models.BooleanField(
        default=True,
        verbose_name="Estado Instalaciones",
        help_text="True = Conforme, False = Con observaciones"
    )
    
    # Observaciones
    observaciones = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Observaciones",
        help_text="Observaciones detectadas durante la entrega"
    )
    plazo_correcciones = models.PositiveIntegerField(
        default=30,
        verbose_name="Plazo para Correcciones (días)",
        help_text="Días calendario para subsanar observaciones"
    )
    
    # Datos adicionales de la vivienda para el acta
    superficie_construida = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        verbose_name="Superficie Construida (m²)"
    )
    numero_ambientes = models.PositiveIntegerField(
        verbose_name="Número de Ambientes"
    )
    
    TIPOS_ESTRUCTURA = [
        ('madera', 'Madera'),
        ('metalica', 'Metálica'),
        ('mixta', 'Mixta'),
        ('hormigon', 'Hormigón'),
    ]
    tipo_estructura = models.CharField(
        max_length=20, 
        choices=TIPOS_ESTRUCTURA,
        verbose_name="Tipo de Estructura"
    )
    
    # Servicios básicos
    tiene_electricidad = models.BooleanField(default=False)
    tiene_agua_potable = models.BooleanField(default=False)
    tiene_alcantarillado = models.BooleanField(default=False)
    # Nota: Campos de gas y lecturas fueron removidos para coincidir con el esquema actual de la BD
    
    # Estado de entrega
    entregado_beneficiario = models.BooleanField(default=False, verbose_name="Entregado al Beneficiario")
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Auto-asignar proyecto y beneficiario desde la vivienda
        if self.vivienda:
            self.proyecto = self.vivienda.proyecto
            if self.vivienda.beneficiario:
                self.beneficiario = self.vivienda.beneficiario
        
        # Generar número de acta automáticamente si no existe
        if not self.numero_acta:
            year = self.fecha_entrega.year if self.fecha_entrega else 2025
            count = ActaRecepcion.objects.filter(
                fecha_entrega__year=year
            ).count() + 1
            self.numero_acta = f"ACT-{year}-{count:03d}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Acta {self.numero_acta} - {self.vivienda}"
    
    class Meta:
        verbose_name = "Acta de Recepción"
        verbose_name_plural = "Actas de Recepción"
        ordering = ['-fecha_creacion']


class FamiliarBeneficiario(models.Model):
    """Modelo para los familiares del beneficiario en el acta"""
    
    acta_recepcion = models.ForeignKey(
        ActaRecepcion,
        on_delete=models.CASCADE,
        related_name='familiares'
    )
    nombre_completo = models.CharField(max_length=150)
    parentesco = models.CharField(max_length=50)
    rut = models.CharField(max_length=12, blank=True, null=True)
    edad = models.PositiveIntegerField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.nombre_completo} - {self.parentesco}"
    
    class Meta:
        verbose_name = "Familiar del Beneficiario"
        verbose_name_plural = "Familiares del Beneficiario"


# TEMPORALMENTE COMENTADO HASTA RESOLVER MIGRACIONES
# class ConstructorActa(models.Model):
#     """Información del constructor para el acta"""
#     
#     acta = models.OneToOneField(
#         ActaRecepcion, 
#         on_delete=models.CASCADE, 
#         related_name='constructor_info'
#     )
#     constructora = models.ForeignKey(
#         Constructora, 
#         on_delete=models.PROTECT,
#         blank=True, 
#         null=True
#     )
#     nombre_empresa = models.CharField(max_length=150)
#     representante = models.CharField(max_length=100)
#     rut = models.CharField(max_length=12)
#     telefono = models.CharField(max_length=20)
#     
#     def save(self, *args, **kwargs):
#         # Auto-llenar desde constructora si existe
#         if self.constructora and not self.nombre_empresa:
#             self.nombre_empresa = self.constructora.nombre
#             self.rut = self.constructora.rut or ""
#             self.telefono = self.constructora.telefono or ""
#         
#         super().save(*args, **kwargs)
#     
#     def __str__(self):
#         return f"Constructor - {self.nombre_empresa}"
#     
#     class Meta:
#         verbose_name = "Constructor del Acta"
#         verbose_name_plural = "Constructores del Acta"