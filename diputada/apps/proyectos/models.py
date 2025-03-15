from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
from django.core.exceptions import ValidationError
from django.utils.html import escape

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return escape(self.nombre)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

class Proyecto(models.Model):
    TIPO_CHOICES = [
        ('ley', 'Proyecto de Ley'),
        ('resolucion', 'Proyecto de Resolución'),
    ]
    
    numero = models.CharField(max_length=20, unique=True, help_text="Formato: XXXX/XX")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='ley')
    titulo = models.CharField(max_length=200)
    descripcion = RichTextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_tipo_display()} {self.numero} {self.titulo}"

    def save(self, *args, **kwargs):
        # Eliminar validación de permisos por categoría
        # Todos los asesores pueden crear proyectos en cualquier categoría
        super().save(*args, **kwargs)

    def clean(self):
        # Validar formato del número
        if self.numero:
            if not '/' in self.numero:
                raise ValidationError({'numero': 'El número debe tener formato XXXX/XX'})

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

class Temario(models.Model):
    numero = models.IntegerField()
    comision = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='temarios_creados'
    )
    proyectos = models.ManyToManyField(Proyecto, through='ProyectoTemario')
    
    class Meta:
        unique_together = ['numero', 'comision']
        verbose_name = 'Temario'
        verbose_name_plural = 'Temarios'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Temario {self.numero} - {self.comision}"

class ProyectoTemario(models.Model):
    proyecto = models.ForeignKey(
        Proyecto, 
        on_delete=models.CASCADE,
        related_name='temarios_asociados'
    )
    temario = models.ForeignKey(Temario, on_delete=models.CASCADE)
    orden = models.PositiveIntegerField()
    
    class Meta:
        ordering = ['orden']
        unique_together = ['temario', 'orden']

    def reordenar_despues_de_eliminar(self):
        """Reordena los proyectos después de eliminar uno"""
        proyectos_posteriores = ProyectoTemario.objects.filter(
            temario=self.temario,
            orden__gt=self.orden
        )
        for pt in proyectos_posteriores:
            pt.orden -= 1
            pt.save()