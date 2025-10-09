from django import forms
from .models import Region, Comuna, Rol, Constructora, Usuario
from proyectos.models import Vivienda
from incidencias.models import Observacion
from django.contrib.auth.forms import UserCreationForm

class RegionForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = ['nombre', 'codigo', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ComunaForm(forms.ModelForm):
    class Meta:
        model = Comuna
        fields = ['nombre', 'region', 'codigo', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'region': forms.Select(attrs={'class': 'form-select'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class RolForm(forms.ModelForm):
    class Meta:
        model = Rol
        fields = ['nombre', 'descripcion', 'activo']
        widgets = {
            'nombre': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ConstructoraForm(forms.ModelForm):
    class Meta:
        model = Constructora
        fields = ['nombre', 'direccion', 'rut', 'region', 'comuna', 'contacto', 'telefono', 'email', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'rut': forms.TextInput(attrs={'class': 'form-control'}),
            'region': forms.Select(attrs={'class': 'form-select'}),
            'comuna': forms.Select(attrs={'class': 'form-select'}),
            'contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class UsuarioForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Dejar en blanco para mantener la contraseña actual (solo edición)'
    )
    confirm_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Confirmar contraseña'
    )
    
    class Meta:
        model = Usuario
        fields = ['email', 'nombre', 'telefono', 'rol', 'region', 'comuna', 'empresa', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'region': forms.Select(attrs={'class': 'form-select'}),
            'comuna': forms.Select(attrs={'class': 'form-select'}),
            'empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and password != confirm_password:
            raise forms.ValidationError('Las contraseñas no coinciden')
        
        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        password = self.cleaned_data.get('password')
        
        if password:
            usuario.set_password(password)
        
        if commit:
            usuario.save()
        
        return usuario

class ViviendaForm(forms.ModelForm):
    class Meta:
        model = Vivienda
        fields = ['proyecto', 'codigo', 'familia_beneficiaria', 'beneficiario', 'tipologia', 'estado', 'fecha_entrega', 'observaciones_generales', 'activa']
        widgets = {
            'proyecto': forms.Select(attrs={'class': 'form-select'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'familia_beneficiaria': forms.TextInput(attrs={'class': 'form-control'}),
            'beneficiario': forms.Select(attrs={'class': 'form-select'}),
            'tipologia': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'fecha_entrega': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observaciones_generales': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ObservacionForm(forms.ModelForm):
    class Meta:
        model = Observacion
        fields = ['proyecto', 'vivienda', 'recinto', 'elemento', 'tipo', 'detalle', 'estado', 'prioridad', 'es_urgente', 'fecha_vencimiento', 'observaciones_seguimiento', 'archivo_adjunto', 'activo']
        widgets = {
            'proyecto': forms.Select(attrs={'class': 'form-select'}),
            'vivienda': forms.Select(attrs={'class': 'form-select'}),
            'recinto': forms.Select(attrs={'class': 'form-select'}),
            'elemento': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'detalle': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'prioridad': forms.Select(attrs={'class': 'form-select'}),
            'es_urgente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fecha_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observaciones_seguimiento': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'archivo_adjunto': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif,.bmp'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'detalle': 'Descripción',
            'fecha_vencimiento': 'Fecha Límite',
            'observaciones_seguimiento': 'Notas de Seguimiento',
            'archivo_adjunto': 'Archivo Adjunto (PDF, DOC, Imagen - máx. 10MB)',
        }


class ConfiguracionObservacionForm(forms.ModelForm):
    class Meta:
        model = __import__('core.models', fromlist=['ConfiguracionObservacion']).ConfiguracionObservacion
        fields = ['dias_vencimiento_normal', 'horas_vencimiento_urgente']
        widgets = {
            'dias_vencimiento_normal': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1',
                'placeholder': '120'
            }),
            'horas_vencimiento_urgente': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1',
                'placeholder': '48'
            }),
        }
        labels = {
            'dias_vencimiento_normal': 'Días de vencimiento (Observaciones Normales)',
            'horas_vencimiento_urgente': 'Horas de vencimiento (Observaciones Urgentes)',
        }
        help_texts = {
            'dias_vencimiento_normal': 'Cantidad de días por defecto para observaciones normales',
            'horas_vencimiento_urgente': 'Cantidad de horas por defecto para observaciones urgentes',
        }