from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash  # Agregamos estas funciones
from django.contrib import messages
from django.contrib.auth.models import User
from apps.proyectos.models import Categoria
from .models import Perfil
from .forms import AsesorCreationForm, DiputadaCreationForm, CategoriaForm
from django.views.decorators.csrf import csrf_protect
from django.db import transaction

def es_diputada(user):
    return user.is_superuser or (hasattr(user, 'perfil') and user.perfil.es_diputada)

def es_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(es_diputada)
def gestion_usuarios(request):
    categorias = Categoria.objects.all()
    asesores = User.objects.filter(
        perfil__es_diputada=False
    ).select_related('perfil').prefetch_related('perfil__categorias')
    
    context = {
        'asesores': asesores,
        'categorias': categorias,
        'is_superuser': request.user.is_superuser,
        'form_asesor': AsesorCreationForm(),
        'form_diputada': DiputadaCreationForm(),
        'categoria_form': CategoriaForm(),
    }
    
    return render(request, 'usuario/gestion.html', context)

@login_required
@user_passes_test(es_diputada)
@csrf_protect
def crear_asesor(request):
    if request.method == 'POST':
        form = AsesorCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Crear y guardar el usuario
                    user = form.save()
                    
                    # 2. Obtener o crear el perfil
                    perfil, created = Perfil.objects.get_or_create(user=user)
                    perfil.es_diputada = False
                    perfil.save()
                    
                    # 3. Asignar categorías
                    categorias = form.cleaned_data.get('categorias')
                    if categorias:
                        perfil.categorias.set(categorias)  # Usar set() en lugar de add()
                
                messages.success(request, f'Asesor {user.get_full_name()} creado exitosamente.')
                
            except Exception as e:
                messages.error(request, f'Error al crear el asesor: {str(e)}')
            
            return redirect('usuario:gestion')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
    
    return redirect('usuario:gestion')

@login_required
@user_passes_test(es_diputada)
def editar_asesor(request, pk):
    asesor = get_object_or_404(User, pk=pk, perfil__es_diputada=False)
    if request.method == 'POST':
        try:
            # Actualizar datos básicos
            asesor.first_name = request.POST.get('first_name')
            asesor.last_name = request.POST.get('last_name')
            asesor.email = request.POST.get('email')
            asesor.save()
            
            # Actualizar categorías
            categorias_ids = request.POST.getlist('categorias')
            if categorias_ids:
                perfil = asesor.perfil
                perfil.categorias.set(categorias_ids)
            
            messages.success(request, 'Asesor actualizado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al actualizar el asesor: {str(e)}')
    
    return redirect('usuario:gestion')

@login_required
@user_passes_test(es_diputada)
@csrf_protect
def eliminar_asesor(request, pk):
    asesor = get_object_or_404(User, pk=pk, perfil__es_diputada=False)
    if request.method == 'POST':
        try:
            # Primero eliminamos los proyectos asociados
            from apps.proyectos.models import Proyecto
            Proyecto.objects.filter(creado_por=asesor).delete()
            
            # Eliminamos el usuario y su perfil
            asesor.delete()
            messages.success(request, 'Asesor eliminado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar el asesor: {str(e)}')
    return redirect('usuario:gestion')

@login_required
@user_passes_test(es_diputada)
def crear_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f'Categoría {categoria.nombre} creada exitosamente.')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    
    return redirect('usuario:gestion')

@login_required
@user_passes_test(es_superuser)
def editar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada exitosamente.')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    return redirect('usuario:gestion')

@login_required
@user_passes_test(es_superuser)
def eliminar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        try:
            categoria.delete()
            messages.success(request, 'Categoría eliminada exitosamente.')
        except:
            messages.error(request, 'No se puede eliminar esta categoría porque está en uso.')
    return redirect('usuario:gestion')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido/a {user.get_full_name() or user.username}!')
            return redirect('index')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'usuario/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('usuario:login')

@login_required
def perfil_view(request):
    return render(request, 'usuario/perfil.html')

@login_required
def cambiar_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        # Validar que todos los campos estén presentes
        if not all([old_password, new_password1, new_password2]):
            messages.error(request, 'Todos los campos son requeridos.')
            return redirect('usuario:perfil')

        # Validar que la contraseña actual sea correcta
        if not request.user.check_password(old_password):
            messages.error(request, 'La contraseña actual es incorrecta.')
            return redirect('usuario:perfil')

        # Validar que las nuevas contraseñas coincidan
        if new_password1 != new_password2:
            messages.error(request, 'Las nuevas contraseñas no coinciden.')
            return redirect('usuario:perfil')

        # Validar longitud mínima
        if len(new_password1) < 8:
            messages.error(request, 'La nueva contraseña debe tener al menos 8 caracteres.')
            return redirect('usuario:perfil')

        try:
            # Cambiar la contraseña
            request.user.set_password(new_password1)
            request.user.save()
            
            # Actualizar la sesión para que el usuario no sea desconectado
            update_session_auth_hash(request, request.user)
            
            messages.success(request, 'Contraseña actualizada exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al cambiar la contraseña: {str(e)}')

    return redirect('usuario:perfil')

@login_required
@user_passes_test(es_superuser)
@csrf_protect
def crear_diputada(request):
    if request.method == 'POST':
        form = DiputadaCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Crear y guardar el usuario
                    user = form.save()
                    
                    # 2. Actualizar el perfil existente (creado por la señal)
                    perfil = user.perfil
                    perfil.es_diputada = True
                    perfil.save()
                
                messages.success(request, f'Diputada {user.get_full_name()} creada exitosamente.')
            except Exception as e:
                messages.error(request, f'Error al crear la diputada: {str(e)}')
            return redirect('usuario:gestion')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error en {field}: {error}')
    
    return redirect('usuario:gestion')