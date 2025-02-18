from django.urls import path
from . import views

app_name = 'usuario'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),
    path('gestion/', views.gestion_usuarios, name='gestion'),
    path('gestion/asesor/crear/', views.crear_asesor, name='crear_asesor'),
    path('gestion/asesor/<int:pk>/editar/', views.editar_asesor, name='editar_asesor'),
    path('gestion/asesor/<int:pk>/eliminar/', views.eliminar_asesor, name='eliminar_asesor'),
    path('gestion/categoria/crear/', views.crear_categoria, name='crear_categoria'),
    path('gestion/categoria/<int:pk>/editar/', views.editar_categoria, name='editar_categoria'),
    path('gestion/categoria/<int:pk>/eliminar/', views.eliminar_categoria, name='eliminar_categoria'),
    path('cambiar-password/', views.cambiar_password, name='cambiar_password'),
    path('gestion/diputada/crear/', views.crear_diputada, name='crear_diputada'),
]