from django import forms
from .models import Proyecto, Actualizacion, Categoria, Temario
from ckeditor.widgets import CKEditorWidget
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django.core.exceptions import ValidationError

class ProyectoForm(forms.ModelForm):
    # Añadir campo para seleccionar comisiones de la ruta
    comisiones_ruta = forms.ModelMultipleChoiceField(
        queryset=Categoria.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Seleccione las comisiones por las que debe pasar este proyecto'
    )
    
    class Meta:
        model = Proyecto
        fields = ['numero', 'tipo', 'titulo', 'descripcion', 'categoria', 'comisiones_ruta']
        widgets = {
            'numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 2323/23'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': CKEditorWidget(),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)
        
        # Mostrar todas las categorías a todos los usuarios
        self.fields['categoria'].queryset = Categoria.objects.all()
        
        # Si estamos editando un proyecto existente, preseleccionar las comisiones de su ruta
        if instance:
            self.fields['comisiones_ruta'].initial = instance.ruta_comisiones.all().values_list('comision', flat=True)
    
    def clean_numero(self):
        numero = self.cleaned_data.get('numero')
        if numero:
            # Verificar si ya existe un proyecto con este número (excepto en edición)
            if Proyecto.objects.filter(numero=numero).exists():
                if not self.instance.pk or self.instance.numero != numero:
                    raise ValidationError('Ya existe un proyecto con este número.')
            
            # Verificar formato
            if '/' not in numero:
                raise ValidationError('El número debe tener formato XXXX/XX')
        return numero

class ActualizacionForm(forms.ModelForm):
    contenido = forms.CharField(widget=CKEditorWidget())
    
    class Meta:
        model = Actualizacion
        fields = ['contenido']

class ProyectoFilterForm(forms.Form):
    numero = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por número...'
        })
    )
    
    busqueda = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por título...'
        })
    )
    
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        required=False,
        empty_label="Todas las comisiones",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

class TemarioForm(forms.ModelForm):
    class Meta:
        model = Temario
        fields = ['numero', 'comision']
        widgets = {
            'numero': forms.NumberInput(attrs={'class': 'form-control'}),
            'comision': forms.Select(attrs={'class': 'form-control'})
        }
        labels = {
            'comision': 'Categoría'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comision'].queryset = Categoria.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        numero = cleaned_data.get('numero')
        comision = cleaned_data.get('comision')
        
        # Verificar que no exista otro temario con el mismo número en la misma comisión
        if numero and comision:
            if Temario.objects.filter(numero=numero, comision=comision).exists():
                if not self.instance.pk or \
                   self.instance.numero != numero or \
                   self.instance.comision != comision:
                    raise forms.ValidationError(
                        'Ya existe un temario con este número en esta comisión'
                    )
        return cleaned_data

class TemarioFilterForm(forms.Form):
    numero = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por número...'
        })
    )
    
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        required=False,
        empty_label="Todas las comisiones",
        widget=forms.Select(attrs={'class': 'form-control'})
    )