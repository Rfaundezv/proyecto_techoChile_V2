from django import forms
from django.forms import ModelForm
from .models import ActaRecepcion, FamiliarBeneficiario
from proyectos.models import Proyecto, Vivienda, Beneficiario
from core.validators import validar_rut
from datetime import datetime


class ActaRecepcionForm(ModelForm):
    """Formulario para crear y editar Actas de Recepción"""
    
    # Campo adicional para búsqueda por RUT
    rut_beneficiario = forms.CharField(
        max_length=12,
        validators=[validar_rut],
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '12.345.678-9',
            'id': 'id_rut_beneficiario'
        }),
        help_text="Ingrese el RUT del beneficiario para auto-completar los datos"
    )
    
    class Meta:
        model = ActaRecepcion
        fields = [
            'numero_acta',
            'vivienda',
            'proyecto',
            'beneficiario',
            'fecha_entrega',
            'lugar_entrega',
            'representante_techo',
            'cargo_representante', 
            'rut_representante',
            'telefono_representante',
            'jefe_construccion',
            'superficie_construida',
            'numero_ambientes',
            'tipo_estructura',
            'estado_estructura',
            'estado_instalaciones',
            'tiene_electricidad',
            'tiene_agua_potable',
            'tiene_alcantarillado',
            'entregado_beneficiario',
            'observaciones',
            'plazo_correcciones'
        ]
        
        widgets = {
            'numero_acta': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: ACT-2025-001'
            }),
            'vivienda': forms.Select(attrs={
                'class': 'form-control'
            }),
            'fecha_entrega': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'lugar_entrega': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección exacta de la entrega'
            }),
            'representante_techo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo del representante'
            }),
            'cargo_representante': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cargo del representante'
            }),
            'rut_representante': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12.345.678-9'
            }),
            'telefono_representante': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+56 9 1234 5678'
            }),
            'jefe_construccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del jefe de construcción (opcional)'
            }),
            'superficie_construida': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'numero_ambientes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'tipo_estructura': forms.Select(attrs={
                'class': 'form-control'
            }),
            'estado_estructura': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'estado_instalaciones': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'tiene_electricidad': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'tiene_agua_potable': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'tiene_alcantarillado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'entregado_beneficiario': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'proyecto': forms.Select(attrs={
                'class': 'form-control'
            }),
            'beneficiario': forms.Select(attrs={
                'class': 'form-control'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Observaciones detectadas durante la entrega...'
            }),
            'plazo_correcciones': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            })
        }
        
        labels = {
            'numero_acta': 'Número de Acta',
            'vivienda': 'Vivienda',
            'fecha_entrega': 'Fecha y Hora de Entrega',
            'lugar_entrega': 'Lugar de Entrega',
            'representante_techo': 'Representante TECHO',
            'cargo_representante': 'Cargo del Representante',
            'rut_representante': 'RUT del Representante',
            'telefono_representante': 'Teléfono del Representante',
            'jefe_construccion': 'Jefe de Construcción',
            'superficie_construida': 'Superficie Construida (m²)',
            'numero_ambientes': 'Número de Ambientes',
            'tipo_estructura': 'Tipo de Estructura',
            'estado_estructura': 'Estado Estructura Conforme',
            'estado_instalaciones': 'Estado Instalaciones Conforme',
            'tiene_electricidad': 'Tiene Electricidad',
            'tiene_agua_potable': 'Tiene Agua Potable',
            'tiene_alcantarillado': 'Tiene Alcantarillado',
            'entregado_beneficiario': 'Entregado al Beneficiario',
            'proyecto': 'Proyecto',
            'beneficiario': 'Beneficiario',
            'observaciones': 'Observaciones',
            'plazo_correcciones': 'Plazo para Correcciones (días)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Generar número de acta automáticamente si está vacío
        if not self.instance.pk and not self.initial.get('numero_acta'):
            # Generar número automático
            ultimo_numero = ActaRecepcion.objects.count() + 1
            fecha_actual = datetime.now()
            numero_acta = f"ACT-{fecha_actual.year}-{ultimo_numero:03d}"
            self.fields['numero_acta'].initial = numero_acta
            
        # Establecer fecha y hora actual por defecto para nuevas actas
        if not self.instance.pk and not self.initial.get('fecha_entrega'):
            self.fields['fecha_entrega'].initial = datetime.now()
            
        # Establecer plazo por defecto de 120 días
        if not self.instance.pk and not self.initial.get('plazo_correcciones'):
            self.fields['plazo_correcciones'].initial = 120

        # Configurar querysets para los campos relacionados
        self.fields['vivienda'].queryset = Vivienda.objects.filter(
            activa=True
        ).select_related('proyecto', 'beneficiario')
        self.fields['vivienda'].empty_label = "Selecciona una vivienda"
        
        self.fields['proyecto'].queryset = Proyecto.objects.filter(
            activo=True
        ).order_by('nombre')
        self.fields['proyecto'].empty_label = "Selecciona un proyecto"
        
        self.fields['beneficiario'].queryset = Beneficiario.objects.filter(
            activo=True
        ).order_by('nombre')
        self.fields['beneficiario'].empty_label = "Selecciona un beneficiario"

    def clean_numero_acta(self):
        """Validar que el número de acta sea único"""
        numero_acta = self.cleaned_data.get('numero_acta')
        
        # Verificar si ya existe (excluyendo la instancia actual en caso de edición)
        qs = ActaRecepcion.objects.filter(numero_acta=numero_acta)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
            
        if qs.exists():
            raise forms.ValidationError(f"Ya existe un acta con el número '{numero_acta}'")
            
        return numero_acta

    def clean_rut_beneficiario(self):
        """Validar el RUT del beneficiario para búsqueda"""
        rut = self.cleaned_data.get('rut_beneficiario')
        if rut:
            try:
                beneficiario = Beneficiario.objects.get(rut=rut, activo=True)
                return rut
            except Beneficiario.DoesNotExist:
                raise forms.ValidationError(f"No se encontró beneficiario con RUT {rut}")
        return rut

    def clean(self):
        """Validaciones del formulario completo"""
        cleaned_data = super().clean()
        
        vivienda = cleaned_data.get('vivienda')
        beneficiario = cleaned_data.get('beneficiario')
        rut_beneficiario = cleaned_data.get('rut_beneficiario')
        
        # Si se proporcionó RUT de búsqueda, validar coherencia
        if rut_beneficiario and beneficiario:
            try:
                beneficiario_por_rut = Beneficiario.objects.get(rut=rut_beneficiario)
                if beneficiario_por_rut != beneficiario:
                    raise forms.ValidationError(
                        "El beneficiario seleccionado no coincide con el RUT ingresado para búsqueda."
                    )
            except Beneficiario.DoesNotExist:
                pass  # Ya se validó en clean_rut_beneficiario
        
        # Verificar que no exista otra acta para la misma vivienda
        if vivienda:
            qs_vivienda = ActaRecepcion.objects.filter(vivienda=vivienda)
            if self.instance.pk:
                qs_vivienda = qs_vivienda.exclude(pk=self.instance.pk)
            
            if qs_vivienda.exists():
                if self.instance.pk:
                    # En edición, solo error si se cambia a una vivienda que ya tiene acta
                    if self.instance.vivienda != vivienda:
                        raise forms.ValidationError("Ya existe un acta de recepción para esta vivienda.")
                else:
                    # En creación, siempre validar
                    raise forms.ValidationError("Ya existe un acta de recepción para esta vivienda.")
        
        # Verificar coherencia entre vivienda y beneficiario (solo advertencia)
        if vivienda and beneficiario:
            if hasattr(vivienda, 'beneficiario') and vivienda.beneficiario and vivienda.beneficiario != beneficiario:
                # Solo mostrar como warning, no bloquear el formulario
                print(f"WARNING: El beneficiario {beneficiario} no coincide con el asignado a la vivienda {vivienda.codigo}")
                # Se puede comentar esta línea si es demasiado estricta:
                # self.add_error('beneficiario', f"El beneficiario seleccionado no corresponde a la vivienda {vivienda.codigo}")
        
        return cleaned_data


class FamiliarBeneficiarioForm(ModelForm):
    """Formulario para los familiares del beneficiario"""
    
    class Meta:
        model = FamiliarBeneficiario
        fields = [
            'nombre_completo',
            'parentesco',
            'rut', 
            'edad'
        ]
        
        widgets = {
            'nombre_completo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo del familiar'
            }),
            'rut': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12.345.678-9'
            }),
            'parentesco': forms.Select(attrs={
                'class': 'form-control'
            }),
            'edad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '120'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+56 9 1234 5678'
            })
        }


# Formset para manejar múltiples familiares
from django.forms import formset_factory

FamiliarFormSet = formset_factory(
    FamiliarBeneficiarioForm,
    extra=2,  # Mostrar 2 formularios vacíos adicionales
    can_delete=True
)


class FiltroActasForm(forms.Form):
    """Formulario para filtrar las actas"""
    
    proyecto = forms.ModelChoiceField(
        queryset=Proyecto.objects.filter(activo=True),
        required=False,
        empty_label="Todos los proyectos",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha desde'
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha hasta'
    )
    
    estado = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('entregada', 'Entregadas'),
            ('pendiente', 'Pendientes'),
            ('con_observaciones', 'Con Observaciones')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Estado'
    )
    
    buscar = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por número de acta o beneficiario...'
        }),
        label='Buscar'
    )