from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import FichaPostventa, ArchivoFicha, HistorialFicha
from proyectos.models import Vivienda, Proyecto
from core.models import Usuario


class FichaPostventaForm(forms.ModelForm):
    """
    Formulario para crear y editar fichas de postventa.
    Organizado por secciones para mejor experiencia de usuario.
    """
    
    class Meta:
        model = FichaPostventa
        fields = [
            # Información básica
            'vivienda', 'fecha_evaluacion', 'evaluador',
            
            # Datos de la familia
            'familia_presente', 'jefe_hogar_presente', 'observaciones_familia',
            
            # Servicios básicos
            'agua_potable_funciona', 'electricidad_funciona', 
            'alcantarillado_funciona', 'gas_funciona',
            
            # Evaluación técnica
            'estado_general_vivienda', 'estado_techumbre', 'estado_muros',
            'estado_pisos', 'estado_puertas_ventanas', 'estado_instalacion_electrica',
            'estado_instalacion_sanitaria',
            
            # Evaluación de satisfacción
            'satisfaccion_general', 'satisfaccion_tamano', 'satisfaccion_distribucion',
            'satisfaccion_ubicacion',
            
            # Necesidades
            'requiere_reparaciones', 'detalle_reparaciones',
            'requiere_mejoras', 'detalle_mejoras',
            
            # Seguimiento social
            'adaptacion_familiar', 'integracion_comunitaria',
            'conoce_vecinos', 'participa_organizaciones',
            
            # Acceso a servicios
            'acceso_salud', 'acceso_educacion', 'acceso_transporte', 'acceso_comercio',
            
            # Observaciones
            'observaciones_tecnicas', 'observaciones_sociales', 'recomendaciones',
            
            # Seguimiento
            'requiere_seguimiento', 'fecha_proximo_seguimiento'
        ]
        
        widgets = {
            # Fechas
            'fecha_evaluacion': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'fecha_proximo_seguimiento': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            
            # Select fields con Bootstrap
            'vivienda': forms.Select(attrs={'class': 'form-select'}),
            'evaluador': forms.Select(attrs={'class': 'form-select'}),
            
            # Campos de evaluación con rangos
            'estado_general_vivienda': forms.Select(attrs={'class': 'form-select'}),
            'estado_techumbre': forms.Select(attrs={'class': 'form-select'}),
            'estado_muros': forms.Select(attrs={'class': 'form-select'}),
            'estado_pisos': forms.Select(attrs={'class': 'form-select'}),
            'estado_puertas_ventanas': forms.Select(attrs={'class': 'form-select'}),
            'estado_instalacion_electrica': forms.Select(attrs={'class': 'form-select'}),
            'estado_instalacion_sanitaria': forms.Select(attrs={'class': 'form-select'}),
            
            # Satisfacción
            'satisfaccion_general': forms.Select(attrs={'class': 'form-select'}),
            'satisfaccion_tamano': forms.Select(attrs={'class': 'form-select'}),
            'satisfaccion_distribucion': forms.Select(attrs={'class': 'form-select'}),
            'satisfaccion_ubicacion': forms.Select(attrs={'class': 'form-select'}),
            
            # Aspectos sociales
            'adaptacion_familiar': forms.Select(attrs={'class': 'form-select'}),
            'integracion_comunitaria': forms.Select(attrs={'class': 'form-select'}),
            
            # Acceso a servicios
            'acceso_salud': forms.Select(attrs={'class': 'form-select'}),
            'acceso_educacion': forms.Select(attrs={'class': 'form-select'}),
            'acceso_transporte': forms.Select(attrs={'class': 'form-select'}),
            'acceso_comercio': forms.Select(attrs={'class': 'form-select'}),
            
            # Checkboxes con Bootstrap
            'familia_presente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'jefe_hogar_presente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'agua_potable_funciona': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'electricidad_funciona': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'alcantarillado_funciona': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'gas_funciona': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requiere_reparaciones': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requiere_mejoras': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'conoce_vecinos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'participa_organizaciones': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requiere_seguimiento': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            # TextAreas
            'observaciones_familia': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
            'detalle_reparaciones': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 4}
            ),
            'detalle_mejoras': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 4}
            ),
            'observaciones_tecnicas': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 4}
            ),
            'observaciones_sociales': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 4}
            ),
            'recomendaciones': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 4}
            )
        }
        
        labels = {
            'familia_presente': '¿Familia presente durante la evaluación?',
            'jefe_hogar_presente': '¿Jefe de hogar presente?',
            'agua_potable_funciona': 'Agua potable funcionando',
            'electricidad_funciona': 'Electricidad funcionando',
            'alcantarillado_funciona': 'Alcantarillado funcionando',
            'gas_funciona': 'Gas funcionando',
            'conoce_vecinos': '¿Conoce a sus vecinos?',
            'participa_organizaciones': '¿Participa en organizaciones comunitarias?',
            'requiere_reparaciones': '¿Requiere reparaciones?',
            'requiere_mejoras': '¿Requiere mejoras?',
            'requiere_seguimiento': '¿Requiere seguimiento adicional?'
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar evaluadores solo con rol TECHO
        if Usuario.objects.exists():
            self.fields['evaluador'].queryset = Usuario.objects.filter(
                rol__nombre='TECHO', 
                is_active=True
            ).order_by('nombre')
        
        # Filtrar viviendas activas con proyectos en postventa
        if Vivienda.objects.exists():
            self.fields['vivienda'].queryset = Vivienda.objects.filter(
                activa=True,
                estado__in=['entregada', 'postventa']
            ).select_related('proyecto').order_by('proyecto__codigo', 'codigo')
        
        # Si hay request, preseleccionar evaluador actual si es TECHO
        if self.request and hasattr(self.request, 'user') and self.request.user.is_authenticated:
            if hasattr(self.request.user, 'rol') and self.request.user.rol and self.request.user.rol.nombre == 'TECHO':
                self.initial['evaluador'] = self.request.user

    def clean_fecha_evaluacion(self):
        """Validar que la fecha de evaluación no sea futura"""
        fecha = self.cleaned_data.get('fecha_evaluacion')
        if fecha and fecha > timezone.now().date():
            raise ValidationError('La fecha de evaluación no puede ser futura.')
        return fecha

    def clean_fecha_proximo_seguimiento(self):
        """Validar fecha de próximo seguimiento"""
        fecha_seguimiento = self.cleaned_data.get('fecha_proximo_seguimiento')
        requiere_seguimiento = self.cleaned_data.get('requiere_seguimiento')
        
        if requiere_seguimiento and not fecha_seguimiento:
            raise ValidationError(
                'Debe especificar una fecha para el próximo seguimiento si se requiere seguimiento adicional.'
            )
        
        if fecha_seguimiento:
            if fecha_seguimiento < timezone.now().date():
                raise ValidationError('La fecha de próximo seguimiento no puede ser anterior a hoy.')
        
        return fecha_seguimiento

    def clean_detalle_reparaciones(self):
        """Validar detalle de reparaciones si se marca que requiere"""
        detalle = self.cleaned_data.get('detalle_reparaciones')
        requiere = self.cleaned_data.get('requiere_reparaciones')
        
        if requiere and not detalle:
            raise ValidationError(
                'Debe especificar el detalle de las reparaciones necesarias.'
            )
        
        return detalle

    def clean_detalle_mejoras(self):
        """Validar detalle de mejoras si se marca que requiere"""
        detalle = self.cleaned_data.get('detalle_mejoras')
        requiere = self.cleaned_data.get('requiere_mejoras')
        
        if requiere and not detalle:
            raise ValidationError(
                'Debe especificar el detalle de las mejoras sugeridas.'
            )
        
        return detalle

    def clean_vivienda(self):
        """Validar que la vivienda no tenga ya una ficha activa"""
        vivienda = self.cleaned_data.get('vivienda')
        
        if vivienda:
            # Si estamos editando, excluir la ficha actual
            fichas_existentes = FichaPostventa.objects.filter(vivienda=vivienda, activa=True)
            if self.instance.pk:
                fichas_existentes = fichas_existentes.exclude(pk=self.instance.pk)
            
            if fichas_existentes.exists():
                raise ValidationError(
                    f'La vivienda {vivienda} ya tiene una ficha de postventa activa. '
                    'Solo puede existir una ficha activa por vivienda.'
                )
        
        return vivienda


class FiltroFichasForm(forms.Form):
    """
    Formulario para filtrar fichas de postventa en el listado
    """
    
    proyecto = forms.ModelChoiceField(
        queryset=Proyecto.objects.filter(activo=True),
        required=False,
        empty_label="Todos los proyectos",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    evaluador = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(rol__nombre='TECHO', is_active=True),
        required=False,
        empty_label="Todos los evaluadores",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    requiere_seguimiento = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    estado_minimo = forms.ChoiceField(
        choices=[('', 'Cualquier estado')] + FichaPostventa.ESCALA_EVALUACION,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Estado general mínimo"
    )


class ArchivoFichaForm(forms.ModelForm):
    """
    Formulario para subir archivos adjuntos a las fichas
    """
    
    class Meta:
        model = ArchivoFicha
        fields = ['tipo', 'archivo', 'descripcion']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'})
        }

    def clean_archivo(self):
        """Validar tamaño y tipo de archivo"""
        archivo = self.cleaned_data.get('archivo')
        
        if archivo:
            # Validar tamaño máximo (10MB)
            if archivo.size > 10 * 1024 * 1024:
                raise ValidationError('El archivo no puede ser mayor a 10MB.')
            
            # Validar extensiones permitidas
            extensiones_permitidas = [
                '.jpg', '.jpeg', '.png', '.gif', '.bmp',  # Imágenes
                '.pdf', '.doc', '.docx', '.txt',  # Documentos
                '.dwg', '.dxf'  # Planos
            ]
            
            extension = archivo.name.lower().split('.')[-1] if '.' in archivo.name else ''
            extension_completa = f'.{extension}'
            
            if extension_completa not in extensiones_permitidas:
                raise ValidationError(
                    f'Tipo de archivo no permitido. '
                    f'Extensiones permitidas: {", ".join(extensiones_permitidas)}'
                )
        
        return archivo


class BusquedaFichasForm(forms.Form):
    """
    Formulario de búsqueda avanzada de fichas
    """
    
    termino = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por código de vivienda, proyecto, familia...'
        }),
        label="Término de búsqueda"
    )
    
    proyecto = forms.ModelChoiceField(
        queryset=Proyecto.objects.filter(activo=True),
        required=False,
        empty_label="Cualquier proyecto",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    rango_puntaje_habitabilidad = forms.CharField(
        required=False,
        widget=forms.Select(choices=[
            ('', 'Cualquier puntaje'),
            ('1-2', 'Muy malo - Malo (1-2)'),
            ('3-3', 'Regular (3)'),
            ('4-5', 'Bueno - Muy bueno (4-5)')
        ], attrs={'class': 'form-select'}),
        label="Puntaje de habitabilidad"
    )