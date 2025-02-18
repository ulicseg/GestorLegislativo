from django.urls import path
from . import views

app_name = 'proyectos'

urlpatterns = [
    path('', views.lista_proyectos, name='lista_proyectos'),
    path('crear/', views.crear_proyecto, name='crear_proyecto'),
    path('<int:pk>/', views.detalle_proyecto, name='detalle_proyecto'),
    path('<int:pk>/editar/', views.editar_proyecto, name='editar_proyecto'),
    path('<int:pk>/actualizacion/crear/', views.crear_actualizacion, name='crear_actualizacion'),
    path('actualizacion/<int:pk>/eliminar/', views.eliminar_actualizacion, name='eliminar_actualizacion'),
    path('<int:pk>/eliminar/', views.eliminar_proyecto, name='eliminar_proyecto'),
    # Removemos las rutas que no estamos usando por ahora
    # path('actualizacion/<int:pk>/editar/', views.editar_actualizacion, name='editar_actualizacion'),
    # path('actualizacion/<int:pk>/eliminar/', views.eliminar_actualizacion, name='eliminar_actualizacion'),
]