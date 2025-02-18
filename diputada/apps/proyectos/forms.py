from django import forms
from .models import Proyecto, Actualizacion, Categoria
from ckeditor.widgets import CKEditorWidget

class ProyectoForm(forms.ModelForm):
    descripcion = forms.CharField(widget=CKEditorWidget())
    
    class Meta:
        model = Proyecto
        fields = ['titulo', 'descripcion']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
        }

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
                empty_label="Todas las categorías",
                widget=forms.Select(attrs={'class': 'form-control'})
            )