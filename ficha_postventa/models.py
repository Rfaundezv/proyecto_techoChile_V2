from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from proyectos.models import Vivienda, Proyecto
from core.models import Usuario
from datetime import date


class FichaPostventa(models.Model):
    """
    Ficha de seguimiento individual de postventa para cada vivienda.
    Contiene evaluaciones técnicas, de habitabilidad y seguimiento de la familia.
    """
    
    # === INFORMACIÓN BÁSICA ===
    vivienda = models.OneToOneField(
        Vivienda, 
        on_delete=models.CASCADE, 
        related_name='ficha_postventa',
        verbose_name="Vivienda"
    )
    
    fecha_creacion = models.DateField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    
    fecha_evaluacion = models.DateField(
        default=date.today,
        verbose_name="Fecha de evaluación"
    )
    
    evaluador = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='fichas_evaluadas',
        verbose_name="Evaluador"
    )
    
    # === DATOS DE LA FAMILIA ===
    familia_presente = models.BooleanField(
        default=True,
        verbose_name="¿Familia presente durante evaluación?"
    )
    
    jefe_hogar_presente = models.BooleanField(
        default=False,
        verbose_name="¿Jefe de hogar presente?"
    )
    
    observaciones_familia = models.TextField(
        blank=True,
        verbose_name="Observaciones sobre la familia",
        help_text="Comentarios sobre la presencia y participación de la familia"
    )
    
    # === EVALUACIÓN DE HABITABILIDAD ===
    
    # Servicios básicos
    agua_potable_funciona = models.BooleanField(
        default=True,
        verbose_name="¿Agua potable funcionando correctamente?"
    )
    
    electricidad_funciona = models.BooleanField(
        default=True,
        verbose_name="¿Electricidad funcionando correctamente?"
    )
    
    alcantarillado_funciona = models.BooleanField(
        default=True,
        verbose_name="¿Alcantarillado funcionando correctamente?"
    )
    
    gas_funciona = models.BooleanField(
        default=True,
        verbose_name="¿Gas funcionando correctamente?"
    )
    
    # Estado general de la vivienda
    ESCALA_EVALUACION = [
        (1, 'Muy malo'),
        (2, 'Malo'),
        (3, 'Regular'),
        (4, 'Bueno'),
        (5, 'Muy bueno'),
    ]
    
    estado_general_vivienda = models.IntegerField(
        choices=ESCALA_EVALUACION,
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Estado general de la vivienda"
    )
    
    estado_techumbre = models.IntegerField(
        choices=ESCALA_EVALUACION,
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Estado de la techumbre"
    )
    
    estado_muros = models.IntegerField(
        choices=ESCALA_EVALUACION,
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Estado de los muros"
    )
    
    estado_pisos = models.IntegerField(
        choices=ESCALA_EVALUACION,
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Estado de los pisos"
    )
    
    estado_puertas_ventanas = models.IntegerField(
        choices=ESCALA_EVALUACION,
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Estado de puertas y ventanas"
    )
    
    estado_instalacion_electrica = models.IntegerField(
        choices=ESCALA_EVALUACION,
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Estado instalación eléctrica"
    )
    
    estado_instalacion_sanitaria = models.IntegerField(
        choices=ESCALA_EVALUACION,
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Estado instalación sanitaria"
    )
    
    # === EVALUACIÓN DE SATISFACCIÓN ===
    
    ESCALA_SATISFACCION = [
        (1, 'Muy insatisfecho'),
        (2, 'Insatisfecho'),
        (3, 'Neutral'),
        (4, 'Satisfecho'),
        (5, 'Muy satisfecho'),
    ]
    
    satisfaccion_general = models.IntegerField(
        choices=ESCALA_SATISFACCION,
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Satisfacción general con la vivienda"
    )
    
    satisfaccion_tamano = models.IntegerField(
        choices=ESCALA_SATISFACCION,
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Satisfacción con el tamaño"
    )
    
    satisfaccion_distribucion = models.IntegerField(
        choices=ESCALA_SATISFACCION,
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Satisfacción con la distribución"
    )
    
    satisfaccion_ubicacion = models.IntegerField(
        choices=ESCALA_SATISFACCION,
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Satisfacción con la ubicación"
    )
    
    # === NECESIDADES Y REQUERIMIENTOS ===
    
    requiere_reparaciones = models.BooleanField(
        default=False,
        verbose_name="¿Requiere reparaciones?"
    )
    
    detalle_reparaciones = models.TextField(
        blank=True,
        verbose_name="Detalle de reparaciones necesarias"
    )
    
    requiere_mejoras = models.BooleanField(
        default=False,
        verbose_name="¿Requiere mejoras?"
    )
    
    detalle_mejoras = models.TextField(
        blank=True,
        verbose_name="Detalle de mejoras sugeridas"
    )
    
    # === SEGUIMIENTO SOCIAL ===
    
    NIVEL_ADAPTACION = [
        (1, 'Muy difícil'),
        (2, 'Difícil'),
        (3, 'Regular'),
        (4, 'Buena'),
        (5, 'Muy buena'),
    ]
    
    adaptacion_familiar = models.IntegerField(
        choices=NIVEL_ADAPTACION,
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Nivel de adaptación familiar"
    )
    
    integracion_comunitaria = models.IntegerField(
        choices=NIVEL_ADAPTACION,
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Nivel de integración comunitaria"
    )
    
    conoce_vecinos = models.BooleanField(
        default=False,
        verbose_name="¿Conoce a sus vecinos?"
    )
    
    participa_organizaciones = models.BooleanField(
        default=False,
        verbose_name="¿Participa en organizaciones comunitarias?"
    )
    
    # === ACCESO A SERVICIOS ===
    
    NIVEL_ACCESO = [
        (1, 'Muy difícil'),
        (2, 'Difícil'),
        (3, 'Regular'),
        (4, 'Fácil'),
        (5, 'Muy fácil'),
    ]
    
    acceso_salud = models.IntegerField(
        choices=NIVEL_ACCESO,
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Acceso a servicios de salud"
    )
    
    acceso_educacion = models.IntegerField(
        choices=NIVEL_ACCESO,
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Acceso a educación"
    )
    
    acceso_transporte = models.IntegerField(
        choices=NIVEL_ACCESO,
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Acceso a transporte público"
    )
    
    acceso_comercio = models.IntegerField(
        choices=NIVEL_ACCESO,
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Acceso a comercio básico"
    )
    
    # === OBSERVACIONES GENERALES ===
    
    observaciones_tecnicas = models.TextField(
        blank=True,
        verbose_name="Observaciones técnicas",
        help_text="Comentarios técnicos sobre el estado de la vivienda"
    )
    
    observaciones_sociales = models.TextField(
        blank=True,
        verbose_name="Observaciones sociales",
        help_text="Comentarios sobre aspectos sociales y de adaptación"
    )
    
    recomendaciones = models.TextField(
        blank=True,
        verbose_name="Recomendaciones",
        help_text="Recomendaciones para mejorar la calidad de vida"
    )
    
    # === SEGUIMIENTO ===
    
    requiere_seguimiento = models.BooleanField(
        default=False,
        verbose_name="¿Requiere seguimiento adicional?"
    )
    
    fecha_proximo_seguimiento = models.DateField(
        blank=True,
        null=True,
        verbose_name="Fecha próximo seguimiento"
    )
    
    # === METADATOS ===
    
    activa = models.BooleanField(
        default=True,
        verbose_name="Ficha activa"
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización"
    )
    
    actualizada_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='fichas_actualizadas',
        null=True,
        blank=True,
        verbose_name="Actualizada por"
    )
    
    def __str__(self):
        return f"Ficha Postventa - {self.vivienda}"
    
    @property
    def puntaje_habitabilidad(self):
        """Calcula puntaje promedio de habitabilidad (1-5)"""
        campos_habitabilidad = [
            self.estado_general_vivienda,
            self.estado_techumbre,
            self.estado_muros,
            self.estado_pisos,
            self.estado_puertas_ventanas,
            self.estado_instalacion_electrica,
            self.estado_instalacion_sanitaria,
        ]
        return sum(campos_habitabilidad) / len(campos_habitabilidad)
    
    @property
    def puntaje_satisfaccion(self):
        """Calcula puntaje promedio de satisfacción (1-5)"""
        campos_satisfaccion = [
            self.satisfaccion_general,
            self.satisfaccion_tamano,
            self.satisfaccion_distribucion,
            self.satisfaccion_ubicacion,
        ]
        return sum(campos_satisfaccion) / len(campos_satisfaccion)
    
    @property
    def puntaje_social(self):
        """Calcula puntaje promedio de aspectos sociales (1-5)"""
        campos_sociales = [
            self.adaptacion_familiar,
            self.integracion_comunitaria,
        ]
        return sum(campos_sociales) / len(campos_sociales)
    
    @property
    def servicios_funcionando(self):
        """Cuenta servicios básicos funcionando"""
        servicios = [
            self.agua_potable_funciona,
            self.electricidad_funciona,
            self.alcantarillado_funciona,
            self.gas_funciona,
        ]
        return sum(servicios)
    
    class Meta:
        verbose_name = "Ficha de Postventa"
        verbose_name_plural = "Fichas de Postventa"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['vivienda']),
            models.Index(fields=['fecha_evaluacion']),
            models.Index(fields=['evaluador']),
            models.Index(fields=['requiere_seguimiento']),
        ]


class HistorialFicha(models.Model):
    """
    Historial de cambios en las fichas de postventa
    """
    
    ficha = models.ForeignKey(
        FichaPostventa,
        on_delete=models.CASCADE,
        related_name='historial'
    )
    
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT
    )
    
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    
    campo_modificado = models.CharField(
        max_length=100,
        verbose_name="Campo modificado"
    )
    
    valor_anterior = models.TextField(
        blank=True,
        verbose_name="Valor anterior"
    )
    
    valor_nuevo = models.TextField(
        blank=True,
        verbose_name="Valor nuevo"
    )
    
    observaciones = models.TextField(
        blank=True,
        verbose_name="Observaciones del cambio"
    )
    
    def __str__(self):
        return f"Cambio en {self.ficha} - {self.campo_modificado}"
    
    class Meta:
        verbose_name = "Historial de Ficha"
        verbose_name_plural = "Historial de Fichas"
        ordering = ['-fecha_cambio']


class ArchivoFicha(models.Model):
    """
    Archivos adjuntos para las fichas (fotos, documentos, etc.)
    """
    
    TIPO_ARCHIVO = [
        ('foto_general', 'Foto General'),
        ('foto_problema', 'Foto de Problema'),
        ('documento', 'Documento'),
        ('plano', 'Plano'),
        ('otro', 'Otro'),
    ]
    
    ficha = models.ForeignKey(
        FichaPostventa,
        on_delete=models.CASCADE,
        related_name='archivos'
    )
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_ARCHIVO,
        default='foto_general',
        verbose_name="Tipo de archivo"
    )
    
    archivo = models.FileField(
        upload_to='fichas_postventa/%Y/%m/',
        verbose_name="Archivo"
    )
    
    descripcion = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Descripción"
    )
    
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    subido_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT
    )
    
    def __str__(self):
        return f"{self.ficha} - {self.descripcion or self.archivo.name}"
    
    class Meta:
        verbose_name = "Archivo de Ficha"
        verbose_name_plural = "Archivos de Fichas"
        ordering = ['-fecha_subida']
