from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Perfil

class CustomUserCreationForm(UserCreationForm):
    categoria = forms.ModelChoiceField(
        queryset=None,  # Se establecerá en __init__
        required=False,
        help_text='Seleccione una categoría para el asesor. Dejar en blanco si es diputada.'
    )
    es_diputada = forms.BooleanField(
        required=False,
        help_text='Marcar si el usuario es diputada'
    )

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.proyectos.models import Categoria
        self.fields['categoria'].queryset = Categoria.objects.all()
        # Hacer obligatorios estos campos
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True

    def save(self, commit=True):
        user = super().save(commit=False)
        user.save()
        # Actualizar el perfil
        perfil = user.perfil
        perfil.es_diputada = self.cleaned_data.get('es_diputada', False)
        if not perfil.es_diputada:  # Si no es diputada, es asesor
            perfil.categoria = self.cleaned_data.get('categoria')
        perfil.save()
        return user

class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name_plural = 'Perfil'

class CustomUserAdmin(UserAdmin):
    inlines = (PerfilInline,)
    add_form = CustomUserCreationForm
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_tipo_usuario', 'get_categoria')
    list_filter = ('perfil__es_diputada', 'perfil__categorias')
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'first_name', 'last_name', 'email', 'es_diputada', 'categoria'),
        }),
    )

    def get_tipo_usuario(self, obj):
        if hasattr(obj, 'perfil'):
            return 'Diputada' if obj.perfil.es_diputada else 'Asesor'
        return '-'
    get_tipo_usuario.short_description = 'Tipo de Usuario'

    def get_categoria(self, obj):
        return ', '.join([cat.nombre for cat in obj.perfil.categorias.all()]) or 'Sin categoría'
    get_categoria.short_description = 'Categoría'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Si es diputada, solo ve a los asesores
        return qs.filter(perfil__es_diputada=False)

    def has_add_permission(self, request):
        # Solo el superuser y la diputada pueden agregar usuarios
        return request.user.is_superuser or (hasattr(request.user, 'perfil') and request.user.perfil.es_diputada)

    def has_change_permission(self, request, obj=None):
        # Solo el superuser y la diputada pueden modificar usuarios
        return request.user.is_superuser or (hasattr(request.user, 'perfil') and request.user.perfil.es_diputada)

    def has_delete_permission(self, request, obj=None):
        # Solo el superuser y la diputada pueden eliminar usuarios
        return request.user.is_superuser or (hasattr(request.user, 'perfil') and request.user.perfil.es_diputada)

# Re-registrar UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)