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
    path('temarios/', views.listar_temarios, name='listar_temarios'),
    path('temarios/crear/', views.crear_temario, name='crear_temario'),
    path('temarios/<int:pk>/', views.detalle_temario, name='detalle_temario'),
    path('temarios/<int:pk>/editar/', views.editar_temario, name='editar_temario'),
    path('temarios/<int:pk>/eliminar/', views.eliminar_temario, name='eliminar_temario'),
    path('temarios/<int:pk>/pdf/', views.descargar_temario_pdf, name='descargar_temario_pdf'),
    path('mis-proyectos/', views.mis_proyectos, name='mis_proyectos'),
    # Removemos las rutas que no estamos usando por ahora
    # path('actualizacion/<int:pk>/editar/', views.editar_actualizacion, name='editar_actualizacion'),
    # path('actualizacion/<int:pk>/eliminar/', views.eliminar_actualizacion, name='eliminar_actualizacion'),
]