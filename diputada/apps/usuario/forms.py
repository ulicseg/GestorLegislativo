from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from apps.proyectos.models import Categoria

class AsesorCreationForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        required=True
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'categoria')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Simplificar las validaciones de contraseña
        self.fields['password1'].help_text = 'Mínimo 8 caracteres'
        self.fields['password2'].help_text = 'Repita la contraseña'
        
        # Remover validaciones complejas de contraseña
        self.fields['password1'].validators = []

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }