from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Proyecto, Actualizacion
from .forms import ProyectoForm, ActualizacionForm, ProyectoFilterForm
from django.core.paginator import Paginator
from django.db.models import Q

@login_required
def lista_proyectos(request):
    # Obtener proyectos según el rol del usuario
    if request.user.perfil.es_diputada:
        proyectos_list = Proyecto.objects.select_related('categoria', 'creado_por').all()
    else:
        # Para asesores, mostrar solo proyectos de su categoría
        proyectos_list = Proyecto.objects.filter(categoria=request.user.perfil.categoria)
    
    # Inicializar el formulario de filtro con el usuario actual
    filter_form = ProyectoFilterForm(request.GET, user=request.user)
    
    # Aplicar filtros si el formulario es válido
    if filter_form.is_valid():
        busqueda = filter_form.cleaned_data.get('busqueda')
        
        if busqueda:
            proyectos_list = proyectos_list.filter(titulo__icontains=busqueda)
        
        # Solo aplicar filtro de categoría si es diputada
        if request.user.perfil.es_diputada:
            categoria = filter_form.cleaned_data.get('categoria')
            if categoria:
                proyectos_list = proyectos_list.filter(categoria=categoria)
    
    # Ordenar proyectos por fecha de creación
    proyectos_list = proyectos_list.order_by('-fecha_creacion')
    
    # Paginación
    paginator = Paginator(proyectos_list, 10)
    page = request.GET.get('page')
    proyectos = paginator.get_page(page)
    
    context = {
        'proyectos': proyectos,
        'es_diputada': request.user.perfil.es_diputada,
        'filter_form': filter_form
    }
    
    return render(request, 'proyectos/listar_proyectos.html', context)

@login_required
def crear_proyecto(request):
    # Solo asesores pueden crear proyectos
    if request.user.perfil.es_diputada:
        messages.error(request, 'Solo los asesores pueden crear proyectos.')
        return redirect('proyectos:lista_proyectos')
    
    if request.method == 'POST':
        form = ProyectoForm(request.POST)
        if form.is_valid():
            proyecto = form.save(commit=False)
            proyecto.creado_por = request.user
            proyecto.categoria = request.user.perfil.categoria
            proyecto.save()
            messages.success(request, 'Proyecto creado exitosamente.')
            return redirect('proyectos:detalle_proyecto', pk=proyecto.pk)
    else:
        form = ProyectoForm()
    
    return render(request, 'proyectos/crear_proyecto.html', {'form': form})

@login_required
def detalle_proyecto(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    
    # Verificar acceso
    if not request.user.perfil.es_diputada and proyecto.categoria != request.user.perfil.categoria:
        messages.error(request, 'No tienes permiso para ver este proyecto.')
        return redirect('proyectos:lista_proyectos')
    
    actualizaciones = proyecto.actualizaciones.all()
    form_actualizacion = ActualizacionForm()
    
    return render(request, 'proyectos/detalle_proyecto.html', {
        'proyecto': proyecto,
        'actualizaciones': actualizaciones,
        'form_actualizacion': form_actualizacion
    })

@login_required
def editar_proyecto(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    
    # Verificar permisos
    if not request.user.perfil.es_diputada and (
        proyecto.categoria != request.user.perfil.categoria or 
        proyecto.creado_por != request.user
    ):
        messages.error(request, 'No tienes permiso para editar este proyecto.')
        return redirect('proyectos:lista_proyectos')
    
    if request.method == 'POST':
        form = ProyectoForm(request.POST, instance=proyecto)
        if form.is_valid():
            proyecto = form.save(commit=False)
            # Asegurarnos que no se cambie la categoría ni el autor
            proyecto.categoria = request.user.perfil.categoria
            proyecto.creado_por = request.user
            proyecto.save()
            messages.success(request, 'Proyecto actualizado exitosamente.')
            return redirect('proyectos:detalle_proyecto', pk=proyecto.pk)
    else:
        form = ProyectoForm(instance=proyecto)
    
    return render(request, 'proyectos/editar_proyecto.html', {
        'form': form,
        'proyecto': proyecto
    })

@login_required
def crear_actualizacion(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    
    # Verificar permisos
    if not request.user.perfil.es_diputada and proyecto.categoria != request.user.perfil.categoria:
        messages.error(request, 'No tienes permiso para actualizar este proyecto.')
        return redirect('proyectos:lista_proyectos')
    
    if request.method == 'POST':
        form = ActualizacionForm(request.POST)
        if form.is_valid():
            actualizacion = form.save(commit=False)
            actualizacion.proyecto = proyecto
            actualizacion.autor = request.user
            actualizacion.save()
            messages.success(request, 'Actualización agregada exitosamente.')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    
    return redirect('proyectos:detalle_proyecto', pk=pk)

@login_required
def editar_actualizacion(request, pk):
    actualizacion = get_object_or_404(Actualizacion, pk=pk)
    proyecto = actualizacion.proyecto

    # Verificar permisos
    if not request.user.perfil.es_diputada and (
        proyecto.categoria != request.user.perfil.categoria or 
        actualizacion.autor != request.user
    ):
        messages.error(request, 'No tienes permiso para editar esta actualización.')
        return redirect('proyectos:detalle_proyecto', pk=proyecto.pk)

    if request.method == 'POST':
        form = ActualizacionForm(request.POST, instance=actualizacion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Actualización modificada exitosamente.')
            return redirect('proyectos:detalle_proyecto', pk=proyecto.pk)
    else:
        form = ActualizacionForm(instance=actualizacion)

    return render(request, 'proyectos/editar_actualizacion.html', {
        'form': form,
        'actualizacion': actualizacion,
        'proyecto': proyecto
    })

@login_required
def eliminar_actualizacion(request, pk):
    actualizacion = get_object_or_404(Actualizacion, pk=pk)
    proyecto = actualizacion.proyecto
    
    # Verificar que el usuario sea el autor de la actualización o sea diputada
    if request.user == actualizacion.autor or request.user.perfil.es_diputada:
        if request.method == 'POST':
            actualizacion.delete()
            messages.success(request, 'Actualización eliminada exitosamente.')
    else:
        messages.error(request, 'No tienes permiso para eliminar esta actualización.')
    
    return redirect('proyectos:detalle_proyecto', pk=proyecto.pk)

@login_required
def eliminar_proyecto(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    
    # Verificar que el usuario sea el creador del proyecto
    if request.user == proyecto.creado_por:
        if request.method == 'POST':
            proyecto.delete()
            messages.success(request, 'Proyecto eliminado exitosamente.')
            return redirect('proyectos:lista_proyectos')
    else:
        messages.error(request, 'No tienes permiso para eliminar este proyecto.')
    
    return redirect('proyectos:detalle_proyecto', pk=pk)