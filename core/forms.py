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
    confirm_email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label='Confirmar email'
    )
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
        fields = ['email', 'rut', 'nombre', 'apellido_paterno', 'apellido_materno', 'telefono', 'rol', 'region', 'comuna', 'constructora', 'empresa', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 12345678-9'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_paterno': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_materno': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'region': forms.Select(attrs={'class': 'form-select'}),
            'comuna': forms.Select(attrs={'class': 'form-select'}),
            'constructora': forms.Select(attrs={'class': 'form-select'}),
            'empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostrar solo constructoras activas, igual que región y comuna
        self.fields['constructora'].queryset = Constructora.objects.filter(activo=True).order_by('nombre')
        self.fields['region'].queryset = Region.objects.filter(activo=True).order_by('nombre')
        self.fields['comuna'].queryset = Comuna.objects.filter(activo=True).order_by('nombre')
        # Contraseña obligatoria solo en creación
        if not self.instance.pk:
            self.fields['password'].required = True
        else:
            self.fields['password'].required = False

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        email = cleaned_data.get('email')
        confirm_email = cleaned_data.get('confirm_email')
        rol = cleaned_data.get('rol')
        constructora = cleaned_data.get('constructora')
        # Validar contraseña
        if password and password != confirm_password:
            raise forms.ValidationError('Las contraseñas no coinciden')
        # Validar email
        if email and confirm_email and email != confirm_email:
            self.add_error('confirm_email', 'Los correos electrónicos no coinciden')
        # Validar constructora si el rol es CONSTRUCTORA
        if rol and hasattr(rol, 'nombre') and rol.nombre == 'CONSTRUCTORA' and not constructora:
            self.add_error('constructora', 'Debes seleccionar una empresa constructora para este usuario.')
        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        password = self.cleaned_data.get('password')
        constructora = self.cleaned_data.get('constructora')
        
        # Sincronizar campo empresa con constructora para compatibilidad
        if constructora:
            usuario.empresa = constructora.nombre
        elif not self.cleaned_data.get('empresa'):
            # Si no hay constructora ni empresa, limpiar empresa
            usuario.empresa = ''
        
        if password:
            usuario.set_password(password)
        
        if commit:
            usuario.save()
        
        return usuario

class ViviendaForm(forms.ModelForm):
    def clean_beneficiario(self):
        beneficiario = self.cleaned_data.get('beneficiario')
        if beneficiario:
            from proyectos.models import Vivienda
            existe = Vivienda.objects.filter(beneficiario=beneficiario).exclude(pk=self.instance.pk).exists()
            if existe:
                raise forms.ValidationError('Este beneficiario ya tiene una vivienda asignada.')
        return beneficiario
    def save(self, commit=True):
        vivienda = super().save(commit=False)
        # Si familia_beneficiaria está vacío y hay beneficiario, lo llenamos
        if not vivienda.familia_beneficiaria and vivienda.beneficiario:
            vivienda.familia_beneficiaria = vivienda.beneficiario.nombre_completo
        if commit:
            vivienda.save()
        return vivienda
    rut_beneficiario = forms.CharField(
        max_length=12,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 12.345.678-9 o 123456789'
        }),
        help_text='Ingrese el RUT con o sin puntos para buscar automáticamente el beneficiario'
    )

    class Meta:
        model = Vivienda
        fields = ['proyecto', 'codigo', 'beneficiario', 'tipologia', 'estado', 'fecha_entrega', 'observaciones_generales', 'activa']
        widgets = {
            'proyecto': forms.Select(attrs={'class': 'form-select'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
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