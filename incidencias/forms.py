from django import forms
from django.db.models import Q
from proyectos.models import Proyecto, Vivienda, Recinto
from .models import Observacion, TipoObservacion, EstadoObservacion, ArchivoAdjuntoObservacion

class FiltroObservacionForm(forms.Form):
    proyecto = forms.ModelChoiceField(
        queryset=Proyecto.objects.filter(activo=True),
        required=False,
        empty_label="Todos los proyectos",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    numero_vivienda = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Número de vivienda',
            'class': 'form-control'
        })
    )
    estado = forms.ModelChoiceField(
        queryset=EstadoObservacion.objects.all(),
        required=False,
        empty_label="Todos los estados",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    tipo = forms.ModelChoiceField(
        queryset=TipoObservacion.objects.filter(activo=True),
        required=False,
        empty_label="Todos los tipos",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    buscar = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Buscar en elemento, detalle...',
            'class': 'form-control'
        })
    )

class ObservacionForm(forms.ModelForm):
    proyecto = forms.ModelChoiceField(
        queryset=Proyecto.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    vivienda = forms.ModelChoiceField(
        queryset=Vivienda.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    recinto = forms.ModelChoiceField(
        queryset=Recinto.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Seleccionar recinto"
    )
    
    # Campo de selección para elementos disponibles del recinto
    elemento_select = forms.CharField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Elemento del recinto"
    )

    class Meta:
        model = Observacion
        fields = ['proyecto', 'vivienda', 'recinto', 'elemento', 'detalle', 
                  'tipo', 'prioridad', 'es_urgente', 'archivo_adjunto']
        widgets = {
            'elemento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'O escribir manualmente'
            }),
            'detalle': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'prioridad': forms.Select(attrs={'class': 'form-select'}),
            'es_urgente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'archivo_adjunto': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif,.bmp'}),
        }
        labels = {
            'archivo_adjunto': 'Archivo Adjunto (PDF, DOC, Imagen - máx. 10MB)',
            'es_urgente': 'Marcar como Urgente (se resolverá en 48 horas)',
            'elemento': 'Elemento (manual)',
        }
        help_texts = {
            'es_urgente': 'Las observaciones urgentes tienen un plazo de 48 horas. Las normales 120 días.',
        }

    def __init__(self, *args, **kwargs):
        exclude_fields = kwargs.pop('exclude_fields', [])
        super().__init__(*args, **kwargs)

        # Excluir campos si se especifica
        for field in exclude_fields:
            if field in self.fields:
                del self.fields[field]

        if 'proyecto' in self.data:
            try:
                proyecto_id = int(self.data.get('proyecto'))
                self.fields['vivienda'].queryset = Vivienda.objects.filter(proyecto_id=proyecto_id)
                # Obtener tipologías de viviendas del proyecto para recintos
                tipologias = Vivienda.objects.filter(proyecto_id=proyecto_id).values_list('tipologia', flat=True).distinct()
                self.fields['recinto'].queryset = Recinto.objects.filter(tipologia__in=tipologias)
            except (ValueError, TypeError):
                pass

class CambioEstadoForm(forms.Form):
    estado = forms.ModelChoiceField(
        queryset=EstadoObservacion.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Nuevo Estado"
    )
    comentario = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        label="Comentario (opcional)",
        help_text="Agrega un comentario sobre el cambio de estado"
    )

class ArchivoAdjuntoForm(forms.ModelForm):
    class Meta:
        model = ArchivoAdjuntoObservacion
        fields = ['archivo', 'descripcion']
        widgets = {
            'archivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif,.bmp'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del archivo (opcional)'
            }),
        }
        labels = {
            'archivo': 'Seleccionar archivo (PDF, DOC, Imagen - máx. 10MB)',
            'descripcion': 'Descripción',
        }
