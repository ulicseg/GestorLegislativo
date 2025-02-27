from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from apps.proyectos.models import Categoria, Proyecto, Actualizacion, Archivo

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    es_diputada = models.BooleanField(default=False)
    categorias = models.ManyToManyField(Categoria, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()}"

@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.get_or_create(user=instance)

@receiver(pre_delete, sender=User)
def limpiar_usuario(sender, instance, **kwargs):
    """Limpia todas las referencias al usuario antes de eliminarlo"""
    # Eliminar proyectos creados por el usuario
    Proyecto.objects.filter(creado_por=instance).delete()
    
    # Eliminar actualizaciones
    Actualizacion.objects.filter(autor=instance).delete()
    
    # Eliminar archivos
    Archivo.objects.filter(subido_por=instance).delete()