from django import forms
from .models import Proyecto, Actualizacion, Categoria, Temario
from ckeditor.widgets import CKEditorWidget
from ckeditor_uploader.widgets import CKEditorUploadingWidget

class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ['titulo', 'descripcion', 'categoria']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': CKEditorWidget(),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and not user.perfil.es_diputada and not self.instance.pk:
            # Si es un asesor creando un nuevo proyecto, mostrar solo sus categorías
            self.fields['categoria'].queryset = user.perfil.categorias.all()
        else:
            # Si es edición o es diputada, mostrar todas las categorías
            self.fields['categoria'].queryset = Categoria.objects.all()

class ActualizacionForm(forms.ModelForm):
    contenido = forms.CharField(widget=CKEditorWidget())
    
    class Meta:
        model = Actualizacion
        fields = ['contenido']

class ProyectoFilterForm(forms.Form):
    busqueda = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por título...'
        })
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.perfil.es_diputada:
            self.fields['categoria'] = forms.ModelChoiceField(
                queryset=Categoria.objects.all(),
                required=False,
                empty_label="Todas las comisiones",
                widget=forms.Select(attrs={'class': 'form-control'})
            )

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