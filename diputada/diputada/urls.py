from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic import TemplateView

urlpatterns = [
    path('adminsupersecreto/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('usuario/', include('apps.usuario.urls')),
    path('proyectos/', include('apps.proyectos.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
]

# Configuración para servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)