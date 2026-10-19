from django.db import models
from django.db.models import ProtectedError
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

def usuario_tiene_historial(user):
    """True si el usuario creó proyectos, actualizaciones o subió archivos."""
    return (
        Proyecto.objects.filter(creado_por=user).exists()
        or Actualizacion.objects.filter(autor=user).exists()
        or Archivo.objects.filter(subido_por=user).exists()
    )

@receiver(pre_delete, sender=User)
def proteger_historial_usuario(sender, instance, **kwargs):
    """Impide borrar un usuario con historial; hay que desactivarlo (is_active=False)."""
    if usuario_tiene_historial(instance):
        raise ProtectedError(
            f'No se puede eliminar a {instance.username}: tiene proyectos o actualizaciones. '
            'Desactívelo en su lugar para conservar el historial.',
            {instance},
        )