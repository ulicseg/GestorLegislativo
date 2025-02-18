from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

class Proyecto(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = RichTextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    creado_por = models.ForeignKey(User, on_delete=models.PROTECT)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        # Si es un nuevo proyecto, asignar la categoría del asesor automáticamente
        if not self.pk and hasattr(self.creado_por, 'perfil'):
            self.categoria = self.creado_por.perfil.categoria
        super().save(*args, **kwargs)

class Actualizacion(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='actualizaciones')
    autor = models.ForeignKey(User, on_delete=models.PROTECT)
    contenido = RichTextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha']

    def __str__(self):
        return f'Actualización de {self.proyecto.titulo} por {self.autor.get_full_name()}'

class Archivo(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='archivos')
    nombre = models.CharField(max_length=200)
    archivo = models.FileField(upload_to='proyectos/archivos/')
    subido_por = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='archivos_subidos'
    )
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre