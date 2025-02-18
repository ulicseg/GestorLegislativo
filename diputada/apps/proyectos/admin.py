from django.contrib import admin
from .models import Categoria, Proyecto, Actualizacion, Archivo

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)

    def has_add_permission(self, request):
        # Solo el superuser puede crear categorías
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        # Solo el superuser puede modificar categorías
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        # Solo el superuser puede eliminar categorías
        return request.user.is_superuser

class ActualizacionInline(admin.TabularInline):
    model = Actualizacion
    extra = 0

class ArchivoInline(admin.TabularInline):
    model = Archivo
    extra = 0

@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'creado_por', 'fecha_creacion')
    list_filter = ('categoria', 'creado_por')
    search_fields = ('titulo', 'descripcion')
    inlines = [ActualizacionInline, ArchivoInline]
    date_hierarchy = 'fecha_creacion'

@admin.register(Actualizacion)
class ActualizacionAdmin(admin.ModelAdmin):
    list_display = ('proyecto', 'autor', 'fecha')
    list_filter = ('proyecto', 'autor')
    search_fields = ('contenido',)

@admin.register(Archivo)
class ArchivoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'proyecto', 'subido_por', 'fecha_subida')
    list_filter = ('proyecto', 'subido_por')
    search_fields = ('nombre',)