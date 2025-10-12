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
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and user.rol and user.rol.nombre == 'CONSTRUCTORA':
            # Filtrar proyectos solo de la constructora del usuario
            if getattr(user, 'constructora', None):
                self.fields['proyecto'].queryset = Proyecto.objects.filter(
                    activo=True,
                    constructora=user.constructora
                )
            elif getattr(user, 'empresa', None):
                # Fallback al campo legacy
                empresa_usuario = user.empresa.strip().lower()
                self.fields['proyecto'].queryset = Proyecto.objects.filter(
                    activo=True,
                    constructora__nombre__icontains=empresa_usuario
                )
            else:
                self.fields['proyecto'].queryset = Proyecto.objects.none()
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
    
    def __init__(self, *args, **kwargs):
        # Extraer parámetros personalizados antes de llamar a super()
        user = kwargs.pop('user', None)
        exclude_fields = kwargs.pop('exclude_fields', [])
        # Limpiar cualquier otro parámetro no esperado
        kwargs.pop('usuario', None)  # En caso de que se pase por error
        
        super().__init__(*args, **kwargs)
        
        # Excluir campos si se especifica (para familias)
        for field in exclude_fields:
            if field in self.fields:
                del self.fields[field]
        
        # Filtrar proyectos para usuarios de constructora
        if user and hasattr(user, 'rol') and user.rol and user.rol.nombre == 'CONSTRUCTORA':
            if 'proyecto' in self.fields:
                if getattr(user, 'constructora', None):
                    self.fields['proyecto'].queryset = Proyecto.objects.filter(
                        activo=True,
                        constructora=user.constructora
                    )
                elif getattr(user, 'empresa', None):
                    # Fallback al campo legacy
                    empresa_usuario = user.empresa.strip().lower()
                    self.fields['proyecto'].queryset = Proyecto.objects.filter(
                        activo=True,
                        constructora__nombre__icontains=empresa_usuario
                    )
                else:
                    self.fields['proyecto'].queryset = Proyecto.objects.none()
        
        # Si hay datos de proyecto, cargar viviendas y recintos
        if 'proyecto' in self.data and 'vivienda' in self.fields:
            try:
                proyecto_id = int(self.data.get('proyecto'))
                self.fields['vivienda'].queryset = Vivienda.objects.filter(
                    proyecto_id=proyecto_id, 
                    activa=True
                ).order_by('codigo')
                
                # Obtener tipologías de viviendas del proyecto para recintos
                if 'recinto' in self.fields:
                    tipologias = Vivienda.objects.filter(proyecto_id=proyecto_id).values_list('tipologia', flat=True).distinct()
                    self.fields['recinto'].queryset = Recinto.objects.filter(tipologia__in=tipologias)
            except (ValueError, TypeError):
                pass
                
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

class CambioEstadoForm(forms.Form):
    estado = forms.ModelChoiceField(
        queryset=EstadoObservacion.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Nuevo Estado",
        empty_label="Seleccionar estado"
    )
    comentario = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 3,
            'placeholder': 'Agregar comentario sobre el cambio...'
        }),
        required=False,
        label="Comentario",
        help_text="Opcional pero recomendado para seguimiento"
    )
    
    def __init__(self, *args, **kwargs):
        estado_actual = kwargs.pop('estado_actual', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar estados según el estado actual
        if estado_actual:
            queryset = EstadoObservacion.objects.filter(activo=True)
            # Excluir el estado actual de las opciones
            queryset = queryset.exclude(pk=estado_actual.pk)
            self.fields['estado'].queryset = queryset

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
