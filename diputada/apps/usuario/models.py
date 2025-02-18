from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from apps.proyectos.models import Categoria, Proyecto, Actualizacion, Archivo

class Perfil(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='perfil'
    )
    es_diputada = models.BooleanField(default=False)
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='asesores'
    )

    def __str__(self):
        return f'Perfil de {self.user.username} - Categoría: {self.categoria.nombre if self.categoria else "Sin categoría"}'

    def save(self, *args, **kwargs):
        # Si es diputada o superusuario, no debe tener categoría
        if self.es_diputada or self.user.is_superuser:
            self.categoria = None
            self.es_diputada = True
        super().save(*args, **kwargs)

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        # Si es superusuario o está siendo creado como diputada, marcar es_diputada como True
        es_diputada = instance.is_superuser
        Perfil.objects.create(
            user=instance,
            es_diputada=es_diputada,
            categoria=None if es_diputada else None  # Las diputadas no tienen categoría
        )

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    # Asegurarse que el perfil exista
    if not hasattr(instance, 'perfil'):
        Perfil.objects.create(
            user=instance,
            es_diputada=instance.is_superuser,
            categoria=None
        )
    
    # Si el usuario es superusuario o es diputada, asegurarse que su perfil sea correcto
    if instance.is_superuser or (hasattr(instance, 'perfil') and instance.perfil.es_diputada):
        instance.perfil.es_diputada = True
        instance.perfil.categoria = None
        instance.perfil.save()

@receiver(pre_delete, sender=User)
def limpiar_usuario(sender, instance, **kwargs):
    """Limpia todas las referencias al usuario antes de eliminarlo"""
    # Eliminar proyectos creados por el usuario
    Proyecto.objects.filter(creado_por=instance).delete()
    
    # Eliminar actualizaciones
    Actualizacion.objects.filter(autor=instance).delete()
    
    # Eliminar archivos
    Archivo.objects.filter(subido_por=instance).delete()