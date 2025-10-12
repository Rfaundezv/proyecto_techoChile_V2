from django import forms
from core.models import Region, Comuna, Constructora
from .models import Proyecto, Vivienda, TipologiaVivienda, Beneficiario, Telefono

class ProyectoForm(forms.ModelForm):
    constructora_rut = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        help_text='RUT de la constructora seleccionada'
    )
    region = forms.ModelChoiceField(
        queryset=Region.objects.all(), 
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    comuna = forms.ModelChoiceField(
        queryset=Comuna.objects.none(), 
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    constructora = forms.ModelChoiceField(
        queryset=Constructora.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Seleccione una constructora'
    )

    class Meta:
        model = Proyecto
        fields = ['codigo', 'siglas', 'nombre', 'constructora', 'region', 'comuna',
                  'fecha_entrega', 'fecha_termino_postventa', 'coordenadas_s', 
                  'coordenadas_w', 'activo']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'siglas': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_entrega': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_termino_postventa': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'coordenadas_s': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00000001'}),
            'coordenadas_w': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00000001'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Mostrar el RUT de la constructora seleccionada
        if 'constructora' in self.data:
            try:
                constructora_id = int(self.data.get('constructora'))
                constructora = Constructora.objects.filter(pk=constructora_id).first()
                if constructora:
                    self.fields['constructora_rut'].initial = constructora.rut
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.constructora:
            self.fields['constructora_rut'].initial = self.instance.constructora.rut

        if 'region' in self.data:
            try:
                region_id = int(self.data.get('region'))
                self.fields['comuna'].queryset = Comuna.objects.filter(region_id=region_id).order_by('nombre')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.region:
            self.fields['comuna'].queryset = self.instance.region.comunas.order_by('nombre')


    def save(self, commit=True):
        proyecto = super().save(commit=False)
        if commit:
            proyecto.save()
            self.save_m2m()
        return proyecto

class ViviendaForm(forms.ModelForm):
    rut_beneficiario = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 12.345.678-9 o 123456789',
            'id': 'id_rut_beneficiario'
        }),
        help_text='Ingrese el RUT con o sin puntos para buscar automáticamente el beneficiario'
    )
    beneficiario = forms.ModelChoiceField(
        queryset=Beneficiario.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='-- Ninguno --'
    )
    class Meta:
        model = Vivienda
        fields = ['codigo', 'rut_beneficiario', 'familia_beneficiaria', 'beneficiario', 'tipologia', 'estado', 
                  'fecha_entrega', 'observaciones_generales']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'familia_beneficiaria': forms.TextInput(attrs={'class': 'form-control'}),
            'tipologia': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'fecha_entrega': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observaciones_generales': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class BeneficiarioForm(forms.ModelForm):
    telefonos = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 912345678, 987654321'}),
        help_text='Separe múltiples teléfonos con comas'
    )
    class Meta:
        model = Beneficiario
        fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'rut', 'email', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_paterno': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido_materno': forms.TextInput(attrs={'class': 'form-control'}),
            'rut': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'apellido_paterno': 'Apellido Paterno',
            'apellido_materno': 'Apellido Materno',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-cargar telefonos existentes en el campo
        if self.instance.pk:
            telefonos_list = self.instance.telefonos.filter(activo=True).values_list('numero', flat=True)
            self.fields['telefonos'].initial = ', '.join(telefonos_list)

    def save(self, commit=True):
        beneficiario = super().save(commit=commit)
        # manejar telefonos
        telefonos_str = self.cleaned_data.get('telefonos', '')
        # limpiar telefonos existentes
        beneficiario.telefonos.all().delete()
        if telefonos_str:
            numeros = [num.strip() for num in telefonos_str.split(',') if num.strip()]
            for numero in numeros:
                Telefono.objects.create(beneficiario=beneficiario, numero=numero)
        return beneficiario
