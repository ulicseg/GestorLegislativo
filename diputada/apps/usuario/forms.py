from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from apps.proyectos.models import Categoria
from django.core.exceptions import ValidationError

class AsesorCreationForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Simplificar las validaciones de contraseña
        self.fields['password1'].help_text = 'Mínimo 8 caracteres'
        self.fields['password2'].help_text = 'Repita la contraseña'
        
        # Remover validaciones complejas de contraseña
        self.fields['password1'].validators = []

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Eliminar caracteres especiales y espacios
            username = username.replace("'", "").replace('"', "").strip()
            
            # Verificar que el username sea único
            if User.objects.filter(username=username).exists():
                raise ValidationError('Este nombre de usuario ya está en uso.')
            
            # Verificar que solo contenga caracteres permitidos
            if not username.replace("_", "").replace("-", "").isalnum():
                raise ValidationError('El nombre de usuario solo puede contener letras, números, guiones y guiones bajos.')
        
        return username

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DiputadaCreationForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = 'Mínimo 8 caracteres'
        self.fields['password2'].help_text = 'Repita la contraseña'
        self.fields['password1'].validators = []