from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Proyecto, Actualizacion, Temario, ProyectoTemario, Categoria
from .forms import ProyectoForm, ActualizacionForm, ProyectoFilterForm, TemarioForm, TemarioFilterForm
from django.core.paginator import Paginator
from django.db.models import Q
from apps.usuario.views import es_diputada
import json
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO

@login_required
def lista_proyectos(request):
    # Obtener proyectos según el rol del usuario
    if request.user.perfil.es_diputada:
        proyectos_list = Proyecto.objects.select_related('categoria', 'creado_por').all()
    else:
        # Para asesores, mostrar proyectos de todas sus categorías
        proyectos_list = Proyecto.objects.filter(
            categoria__in=request.user.perfil.categorias.all()
        ).select_related('categoria', 'creado_por')
    
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
    if request.method == 'POST':
        form = ProyectoForm(request.POST, user=request.user)
        if form.is_valid():
            proyecto = form.save(commit=False)
            proyecto.creado_por = request.user
            proyecto.save()
            messages.success(request, 'Proyecto creado exitosamente.')
            return redirect('proyectos:detalle_proyecto', pk=proyecto.pk)
    else:
        form = ProyectoForm(user=request.user)
    
    return render(request, 'proyectos/crear_proyecto.html', {'form': form})

@login_required
def detalle_proyecto(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    
    # Verificar acceso
    if not request.user.perfil.es_diputada and proyecto.categoria not in request.user.perfil.categorias.all():
        messages.error(request, 'No tienes permiso para ver este proyecto.')
        return redirect('proyectos:lista_proyectos')
    
    actualizaciones = proyecto.actualizaciones.all()
    # Mostrar formulario de actualización si es diputada o es su proyecto
    puede_actualizar = request.user.perfil.es_diputada or proyecto.creado_por == request.user
    form_actualizacion = ActualizacionForm() if puede_actualizar else None
    
    # Agregar el formulario de actualización
    form = ActualizacionForm()
    
    context = {
        'proyecto': proyecto,
        'actualizaciones': actualizaciones,
        'form_actualizacion': form_actualizacion,
        'puede_actualizar': puede_actualizar,
        'form': form,
    }
    
    return render(request, 'proyectos/detalle_proyecto.html', context)

@login_required
def editar_proyecto(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    
    # Verificar permisos:
    # - Diputadas pueden editar cualquier proyecto
    # - Asesores pueden editar proyectos de sus comisiones
    if not request.user.perfil.es_diputada and proyecto.categoria not in request.user.perfil.categorias.all():
        messages.error(request, 'No tienes permiso para editar este proyecto.')
        return redirect('proyectos:lista_proyectos')
    
    if request.method == 'POST':
        form = ProyectoForm(request.POST, instance=proyecto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proyecto actualizado exitosamente.')
            return redirect('proyectos:detalle_proyecto', pk=proyecto.pk)
    else:
        form = ProyectoForm(instance=proyecto)
        form.fields['categoria'].queryset = Categoria.objects.all()
    
    return render(request, 'proyectos/editar_proyecto.html', {
        'form': form,
        'proyecto': proyecto,
        'todas_categorias': Categoria.objects.all()
    })

@login_required
def crear_actualizacion(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    
    if request.method == 'POST':
        form = ActualizacionForm(request.POST)
        if form.is_valid():
            actualizacion = form.save(commit=False)
            actualizacion.proyecto = proyecto
            actualizacion.autor = request.user
            actualizacion.save()
            messages.success(request, 'Actualización agregada exitosamente.')
            # Corregimos la redirección
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return redirect(referer)
            return redirect('proyectos:detalle_proyecto', pk=proyecto.pk)
    
    messages.error(request, 'Error al agregar la actualización.')
    return redirect('proyectos:detalle_proyecto', pk=proyecto.pk)

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
    
    # Verificar que el usuario sea el creador del proyecto o sea de su comisión
    if request.user == proyecto.creado_por or (
        not request.user.perfil.es_diputada and 
        request.user.perfil.categoria == proyecto.categoria
    ):
        if request.method == 'POST':
            # Obtener todos los ProyectoTemario asociados antes de eliminar
            temarios_afectados = list(proyecto.temarios_asociados.all())
            
            # Reordenar los proyectos en cada temario afectado
            for pt in temarios_afectados:
                pt.reordenar_despues_de_eliminar()

            proyecto.delete()
            messages.success(request, 'Proyecto eliminado exitosamente.')
            
            # Notificar si el proyecto estaba en temarios
            if temarios_afectados:
                messages.warning(
                    request, 
                    'El proyecto fue eliminado de los temarios en los que estaba incluido.'
                )

            return redirect('proyectos:lista_proyectos')
    else:
        messages.error(request, 'No tienes permiso para eliminar este proyecto.')
    
    return redirect('proyectos:detalle_proyecto', pk=pk)

@login_required
def listar_temarios(request):
    temarios = Temario.objects.select_related('comision').prefetch_related('proyectotemario_set__proyecto').order_by('-fecha_creacion')
    
    filter_form = TemarioFilterForm(request.GET)
    if filter_form.is_valid():
        numero = filter_form.cleaned_data.get('numero')
        categoria = filter_form.cleaned_data.get('categoria')
        
        if numero:
            temarios = temarios.filter(numero=numero)
        if categoria:
            temarios = temarios.filter(comision=categoria)
    
    return render(request, 'proyectos/listar_temarios.html', {
        'temarios': temarios,
        'filter_form': filter_form
    })

@login_required
def crear_temario(request):
    if request.method == 'POST':
        form = TemarioForm(request.POST)
        if form.is_valid():
            temario = form.save()
            
            # Procesar los proyectos seleccionados
            proyectos_data = json.loads(request.POST.get('proyectos', '[]'))
            for proyecto_id, datos in proyectos_data:
                ProyectoTemario.objects.create(
                    temario=temario,
                    proyecto_id=proyecto_id,
                    orden=datos['orden']
                )
            
            messages.success(request, 'Temario creado exitosamente.')
            return redirect('proyectos:listar_temarios')
    else:
        form = TemarioForm()
    
    proyectos_disponibles = Proyecto.objects.all()
    return render(request, 'proyectos/crear_temario.html', {
        'form': form,
        'proyectos_disponibles': proyectos_disponibles
    })

@login_required
def editar_temario(request, pk):
    temario = get_object_or_404(Temario, pk=pk)
    
    if request.method == 'POST':
        form = TemarioForm(request.POST, instance=temario)
        if form.is_valid():
            temario = form.save()
            
            # Eliminar relaciones existentes
            ProyectoTemario.objects.filter(temario=temario).delete()
            
            # Crear nuevas relaciones
            proyectos_data = json.loads(request.POST.get('proyectos', '[]'))
            for proyecto_id, datos in proyectos_data:
                ProyectoTemario.objects.create(
                    temario=temario,
                    proyecto_id=proyecto_id,
                    orden=datos['orden']
                )
            
            messages.success(request, 'Temario actualizado exitosamente.')
            return redirect('proyectos:listar_temarios')
    else:
        form = TemarioForm(instance=temario)
    
    proyectos_disponibles = Proyecto.objects.all()
    return render(request, 'proyectos/crear_temario.html', {
        'form': form,
        'temario': temario,
        'proyectos_disponibles': proyectos_disponibles
    })

@login_required
def detalle_temario(request, pk):
    temario = get_object_or_404(Temario, pk=pk)
    proyectos_temario = temario.proyectotemario_set.select_related('proyecto').order_by('orden')
    
    return render(request, 'proyectos/detalle_temario.html', {
        'temario': temario,
        'proyectos_temario': proyectos_temario
    })

@login_required
@user_passes_test(lambda u: u.perfil.es_diputada)
def eliminar_temario(request, pk):
    temario = get_object_or_404(Temario, pk=pk)
    if request.method == 'POST':
        temario.delete()
        messages.success(request, 'Temario eliminado exitosamente.')
    else:
        messages.error(request, 'No tienes permiso para eliminar este temario.')
    return redirect('proyectos:listar_temarios')

@login_required
@user_passes_test(es_diputada)
def mis_proyectos(request):
    proyectos = Proyecto.objects.filter(
        creado_por=request.user
    ).select_related('categoria').order_by('-fecha_creacion')
    
    filter_form = ProyectoFilterForm(request.GET, user=request.user)
    if filter_form.is_valid():
        busqueda = filter_form.cleaned_data.get('busqueda')
        categoria = filter_form.cleaned_data.get('categoria')
        
        if busqueda:
            proyectos = proyectos.filter(
                titulo__icontains=busqueda
            )
        if categoria:
            proyectos = proyectos.filter(categoria=categoria)
    
    paginator = Paginator(proyectos, 10)
    page = request.GET.get('page')
    proyectos = paginator.get_page(page)
    
    context = {
        'proyectos': proyectos,
        'filter_form': filter_form,
        'es_diputada': True,
        'section': 'mis_proyectos'
    }
    
    return render(request, 'proyectos/mis_proyectos.html', context)

@login_required
def descargar_temario_pdf(request, pk):
    temario = get_object_or_404(Temario, pk=pk)
    
    # Verificar permisos
    if not request.user.perfil.es_diputada and not request.user.perfil.categorias.filter(id=temario.comision.id).exists():
        messages.error(request, 'No tienes permiso para ver este temario.')
        return redirect('proyectos:listar_temarios')
    
    # Configurar el documento
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40, 
        bottomMargin=40
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Definir todos los estilos necesarios
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.gray,
        alignment=1,
        spaceBefore=0,
        spaceAfter=5,
        leading=8
    )
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.black,
        spaceAfter=10,
        alignment=1,
        leading=24
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.black,
        spaceBefore=15,
        spaceAfter=10,
        leading=16,
        leftIndent=15
    )
    
    meta_style = ParagraphStyle(
        'MetaInfo',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.gray,
        alignment=1,
        spaceBefore=0,
        spaceAfter=20,
        leading=15
    )
    
    content_style = ParagraphStyle(
        'Content',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceBefore=6,
        spaceAfter=12,
        leftIndent=20,
        rightIndent=20,
        textColor=colors.black
    )
    
    update_style = ParagraphStyle(
        'Update',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        leftIndent=25,
        rightIndent=25,
        textColor=colors.black,
        backColor=colors.Color(0.95, 0.95, 0.95)
    )
    
    author_style = ParagraphStyle(
        'Author',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.gray,
        leftIndent=25,
        rightIndent=25,
        leading=10
    )

    # Convertir fecha a español
    meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
             'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    fecha = temario.fecha_creacion
    fecha_esp = f"{fecha.day} de {meses[fecha.month - 1]} de {fecha.year}"
    
    # Encabezado y título
    elements.append(Paragraph("Sistema de Proyectos Legislativos", header_style))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph(f"Temario #{temario.numero}", title_style))
    elements.append(Paragraph(f"COMISION DE {temario.comision.nombre.upper()}", heading_style))
    elements.append(Paragraph(f"{fecha_esp}", meta_style))
    elements.append(Spacer(1, 20))
    
    # Proyectos
    for i, pt in enumerate(temario.proyectotemario_set.all().select_related(
        'proyecto', 'proyecto__categoria', 'proyecto__creado_por'
    ).prefetch_related('proyecto__actualizaciones', 'proyecto__actualizaciones__autor')):
        
        # Título del proyecto con su número de orden y comisión al lado
        # Convertir el nombre de la categoría a minúsculas y capitalizar la primera letra
        categoria_nombre = pt.proyecto.categoria.nombre.lower().capitalize()
        
        elements.append(Paragraph(
            f"<u>{pt.orden}. {pt.proyecto.titulo}</u> <i><font color='gray'> - {categoria_nombre}</font></i>",
            heading_style
        ))
        
        # Descripción del proyecto
        elements.append(Paragraph(pt.proyecto.descripcion, content_style))
        
        if pt.proyecto.actualizaciones.exists():
            elements.append(Paragraph("Historial de Actualizaciones:", heading_style))
            
            for actualizacion in pt.proyecto.actualizaciones.all():
                fecha_act = actualizacion.fecha
                fecha_act_esp = f"{fecha_act.day} de {meses[fecha_act.month - 1]}"
                
                elements.append(Paragraph(
                    actualizacion.contenido,
                    update_style
                ))
                
                elements.append(Paragraph(
                    f"Por: {actualizacion.autor.get_full_name()} - {fecha_act_esp}",
                    author_style
                ))
                elements.append(Spacer(1, 10))
        
        elements.append(Spacer(1, 15))
    
    # Pie de página
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(
        "____________________",
        meta_style
    ))
    elements.append(Paragraph(
        "Sistema de Proyectos Legislativos",
        meta_style
    ))
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f'Temario_{temario.numero}_{temario.comision.nombre}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response