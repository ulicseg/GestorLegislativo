from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Proyecto, Actualizacion, Temario, ProyectoTemario, Categoria, RutaComision
from .forms import ProyectoForm, ActualizacionForm, ProyectoFilterForm, TemarioForm, TemarioFilterForm
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.db import models
from apps.usuario.views import es_diputada
import json
from django.http import HttpResponse, JsonResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from django.urls import reverse
from bs4 import BeautifulSoup
import re
from html import unescape

def limpiar_html(html_content):
    """Limpia el HTML complejo y lo convierte a un formato simple."""
    if not html_content:
        return ""
    
    # Usar BeautifulSoup para parsear el HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Mantener los saltos de línea
    for br in soup.find_all('br'):
        br.replace_with('\n')
    
    # Convertir estilos de texto
    for tag in soup.find_all(['b', 'strong']):
        tag.replace_with(f'<b>{tag.get_text()}</b>')
    
    for tag in soup.find_all(['i', 'em']):
        tag.replace_with(f'<i>{tag.get_text()}</i>')
    
    for tag in soup.find_all('u'):
        tag.replace_with(f'<u>{tag.get_text()}</u>')
    
    # Obtener el texto y mantener solo las etiquetas básicas
    text = soup.get_text()
    
    # Limpiar espacios extra y caracteres especiales
    text = re.sub(r'\s+', ' ', text).strip()
    text = unescape(text)
    
    return text

@login_required
def lista_proyectos(request):
    # Obtener proyectos según el rol del usuario
    # Ahora todos los usuarios pueden ver todos los proyectos
    proyectos_list = Proyecto.objects.select_related('categoria', 'creado_por').all()
    
    # Inicializar el formulario de filtro con el usuario actual
    filter_form = ProyectoFilterForm(request.GET, user=request.user)
    
    # Aplicar filtros si el formulario es válido
    if filter_form.is_valid():
        busqueda = filter_form.cleaned_data.get('busqueda')
        numero = filter_form.cleaned_data.get('numero')
        categoria = filter_form.cleaned_data.get('categoria')
        
        if busqueda:
            proyectos_list = proyectos_list.filter(titulo__icontains=busqueda)
            
        if numero:
            proyectos_list = proyectos_list.filter(numero__icontains=numero)
        
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
            
            # Verificar si se proporcionó un orden personalizado
            comisiones_orden = request.POST.get('comisiones_orden', '')
            if comisiones_orden:
                # Usar el orden personalizado
                comisiones_ids = comisiones_orden.split(',')
                
                # Crear las rutas para las comisiones seleccionadas en el orden especificado
                for i, comision_id in enumerate(comisiones_ids, start=1):
                    try:
                        comision = Categoria.objects.get(id=comision_id)
                        RutaComision.objects.create(
                            proyecto=proyecto,
                            comision=comision,
                            orden=i,
                            estado='pendiente'
                        )
                    except Categoria.DoesNotExist:
                        continue
            else:
                # Usar el método anterior si no hay orden personalizado
                comisiones_ruta = form.cleaned_data.get('comisiones_ruta', [])
                for i, comision in enumerate(comisiones_ruta, start=1):
                    RutaComision.objects.create(
                        proyecto=proyecto,
                        comision=comision,
                        orden=i,
                        estado='pendiente'
                    )
            
            messages.success(request, 'Proyecto creado exitosamente.')
            return redirect('proyectos:detalle_proyecto', pk=proyecto.pk)
    else:
        form = ProyectoForm(user=request.user)
    
    return render(request, 'proyectos/crear_proyecto.html', {'form': form})

@login_required
def detalle_proyecto(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    from_mis_proyectos = request.GET.get('from') == 'mis_proyectos'
    
    # Eliminar verificación de acceso por comisión
    # Todos los asesores pueden ver todos los proyectos
    
    actualizaciones = proyecto.actualizaciones.all()
    # Todos los usuarios pueden actualizar cualquier proyecto
    puede_actualizar = True
    form_actualizacion = ActualizacionForm()
    
    # Agregar el formulario de actualización
    form = ActualizacionForm()
    
    # Obtener la ruta de comisiones del proyecto
    ruta_comisiones = proyecto.ruta_comisiones.all().order_by('orden')
    
    context = {
        'proyecto': proyecto,
        'actualizaciones': actualizaciones,
        'form_actualizacion': form_actualizacion,
        'puede_actualizar': puede_actualizar,
        'form': form,
        'from_mis_proyectos': from_mis_proyectos,
        'ruta_comisiones': ruta_comisiones,
    }
    
    return render(request, 'proyectos/detalle_proyecto.html', context)

@login_required
def editar_proyecto(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    from_mis_proyectos = request.GET.get('from') == 'mis_proyectos'
    
    # Eliminar verificación de permisos por comisión
    # Todos los asesores pueden editar cualquier proyecto
    
    if request.method == 'POST':
        form = ProyectoForm(request.POST, instance=proyecto)
        if form.is_valid():
            form.save()
            
            # Procesar las comisiones de la ruta
            comisiones_ruta = form.cleaned_data.get('comisiones_ruta', [])
            
            # Verificar si se proporcionó un orden personalizado
            comisiones_orden = request.POST.get('comisiones_orden', '')
            if comisiones_orden:
                # Usar el orden personalizado
                comisiones_ids = comisiones_orden.split(',')
                
                # Eliminar las rutas existentes que no están en la nueva selección
                RutaComision.objects.filter(proyecto=proyecto).exclude(comision__id__in=comisiones_ids).delete()
                
                # Actualizar o crear las rutas para las comisiones seleccionadas en el orden especificado
                for i, comision_id in enumerate(comisiones_ids, start=1):
                    try:
                        comision = Categoria.objects.get(id=comision_id)
                        RutaComision.objects.update_or_create(
                            proyecto=proyecto,
                            comision=comision,
                            defaults={'orden': i}
                        )
                    except Categoria.DoesNotExist:
                        continue
            else:
                # Usar el método anterior si no hay orden personalizado
                # Eliminar las rutas existentes que no están en la nueva selección
                RutaComision.objects.filter(proyecto=proyecto).exclude(comision__in=comisiones_ruta).delete()
                
                # Actualizar o crear las rutas para las comisiones seleccionadas
                for i, comision in enumerate(comisiones_ruta, start=1):
                    RutaComision.objects.update_or_create(
                        proyecto=proyecto,
                        comision=comision,
                        defaults={'orden': i}
                    )
            
            messages.success(request, 'Proyecto actualizado exitosamente.')
            return redirect(f"{reverse('proyectos:detalle_proyecto', args=[proyecto.pk])}{'?from=mis_proyectos' if from_mis_proyectos else ''}")
    else:
        form = ProyectoForm(instance=proyecto)
        form.fields['categoria'].queryset = Categoria.objects.all()
    
    return render(request, 'proyectos/editar_proyecto.html', {
        'form': form,
        'proyecto': proyecto,
        'todas_categorias': Categoria.objects.all(),
        'from_mis_proyectos': from_mis_proyectos
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
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'No tienes permiso para editar esta actualización.'
            }, status=403)
        messages.error(request, 'No tienes permiso para editar esta actualización.')
        return redirect('proyectos:detalle_proyecto', pk=proyecto.pk)

    if request.method == 'POST':
        form = ActualizacionForm(request.POST, instance=actualizacion)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Actualización modificada exitosamente.',
                    'contenido': form.cleaned_data['contenido']
                })
            messages.success(request, 'Actualización modificada exitosamente.')
            return redirect('proyectos:detalle_proyecto', pk=proyecto.pk)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Error al modificar la actualización.',
                    'errors': form.errors
                }, status=400)
            messages.error(request, 'Error al modificar la actualización.')
    else:
        form = ActualizacionForm(instance=actualizacion)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'form': {
                'contenido': form['contenido'].value()
            }
        })

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
    from_mis_proyectos = request.GET.get('from') == 'mis_proyectos'
    
    # Verificar que el usuario sea el creador del proyecto o sea de su comisión
    if request.user == proyecto.creado_por or (
        not request.user.perfil.es_diputada and 
        request.user.perfil.categoria == proyecto.categoria
    ):
        if request.method == 'POST':
            # Obtener todos los ProyectoTemario asociados antes de eliminar
            temarios_afectados = list(proyecto.temarios_asociados.all())
            
            # Eliminar el proyecto (esto eliminará automáticamente sus ProyectoTemario)
            proyecto.delete()
            
            messages.success(request, 'Proyecto eliminado exitosamente.')
            
            # Notificar si el proyecto estaba en temarios
            if temarios_afectados:
                messages.warning(
                    request, 
                    'El proyecto fue eliminado de los temarios en los que estaba incluido.'
                )

            return redirect('proyectos:mis_proyectos' if from_mis_proyectos else 'proyectos:lista_proyectos')
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
def mis_proyectos(request):
    # Si es diputada, mostrar sus proyectos
    if request.user.perfil.es_diputada:
        proyectos = Proyecto.objects.filter(
            creado_por=request.user
        ).select_related('categoria').order_by('-fecha_creacion')
    else:
        # Si es asesor, mostrar todos los proyectos de la diputada sin restricción de comisión
        proyectos = Proyecto.objects.filter(
            creado_por__perfil__es_diputada=True
        ).select_related('categoria').order_by('-fecha_creacion')
    
    filter_form = ProyectoFilterForm(request.GET, user=request.user)
    if filter_form.is_valid():
        busqueda = filter_form.cleaned_data.get('busqueda')
        numero = filter_form.cleaned_data.get('numero')
        categoria = filter_form.cleaned_data.get('categoria')
        
        if busqueda:
            proyectos = proyectos.filter(titulo__icontains=busqueda)
            
        if numero:
            proyectos = proyectos.filter(numero__icontains=numero)
            
        if categoria:
            proyectos = proyectos.filter(categoria=categoria)
    
    paginator = Paginator(proyectos, 10)
    page = request.GET.get('page')
    proyectos = paginator.get_page(page)
    
    context = {
        'proyectos': proyectos,
        'filter_form': filter_form,
        'es_diputada': request.user.perfil.es_diputada,
        'section': 'mis_proyectos'
    }
    
    return render(request, 'proyectos/mis_proyectos.html', context)

@login_required
def descargar_temario_pdf(request, pk):
    temario = get_object_or_404(Temario, pk=pk)
    
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
    
    # Estilo para la sección de ruta de comisiones
    route_title_style = ParagraphStyle(
        'RouteTitle',
        parent=styles['Normal'],
        fontSize=12,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        spaceBefore=12,
        spaceAfter=6,
        leftIndent=20,
        leading=14
    )
    
    route_item_style = ParagraphStyle(
        'RouteItem',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        leftIndent=30,
        rightIndent=30,
        spaceBefore=3,
        spaceAfter=3,
        textColor=colors.black,
        backColor=colors.Color(0.97, 0.97, 0.97),
        borderPadding=5
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
    ).prefetch_related(
        'proyecto__actualizaciones', 
        'proyecto__actualizaciones__autor',
        'proyecto__ruta_comisiones',
        'proyecto__ruta_comisiones__comision'
    )):
        
        # Título del proyecto con su número de orden y comisión al lado
        categoria_nombre = pt.proyecto.categoria.nombre.lower().capitalize()
        
        elements.append(Paragraph(
            f"<u>{pt.orden}. {pt.proyecto.get_tipo_display()} {pt.proyecto.numero} - {pt.proyecto.titulo}</u> <i><font color='gray'> - {categoria_nombre}</font></i>",
            heading_style
        ))
        
        # Descripción del proyecto (limpiada)
        descripcion_limpia = limpiar_html(pt.proyecto.descripcion)
        elements.append(Paragraph(descripcion_limpia, content_style))
        
        # Ruta de comisiones
        rutas = pt.proyecto.ruta_comisiones.all().order_by('orden')
        if rutas.exists():
            elements.append(Paragraph("Ruta de comisiones:", route_title_style))
            elements.append(Spacer(1, 5))
            
            for i, ruta in enumerate(rutas, 1):
                estado_texto = ruta.get_estado_display()
                color_estado = ""
                
                if ruta.estado == 'aprobado':  # Despacho
                    color_estado = "green"
                elif ruta.estado == 'tratandose':  # Archivo
                    color_estado = "orange"
                elif ruta.estado == 'desaprobado':  # En cartera
                    color_estado = "red"
                else:  # Pendiente
                    color_estado = "gray"
                
                elements.append(Paragraph(
                    f'<b>{i}.</b> {ruta.comision.nombre} - <font color="{color_estado}">{estado_texto}</font>',
                    route_item_style
                ))
            
            elements.append(Spacer(1, 10))
        
        if pt.proyecto.actualizaciones.exists():
            elements.append(Paragraph("Historial de Actualizaciones:", heading_style))
            
            for actualizacion in pt.proyecto.actualizaciones.all():
                fecha_act = actualizacion.fecha
                fecha_act_esp = f"{fecha_act.day} de {meses[fecha_act.month - 1]}"
                
                # Limpiar el contenido de la actualización
                contenido_limpio = limpiar_html(actualizacion.contenido)
                elements.append(Paragraph(
                    contenido_limpio,
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
    
    try:
        doc.build(elements)
    except Exception as e:
        messages.error(request, f'Error al generar el PDF: {str(e)}')
        return redirect('proyectos:detalle_temario', pk=temario.pk)
    
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f'Temario_{temario.numero}_{temario.comision.nombre}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@login_required
def cambiar_estado_comision(request, ruta_id):
    """Cambia el estado de un proyecto en una comisión específica."""
    ruta = get_object_or_404(RutaComision, pk=ruta_id)
    proyecto = ruta.proyecto
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in dict(RutaComision.ESTADO_CHOICES):
            ruta.estado = nuevo_estado
            ruta.save()
            messages.success(request, f'Estado actualizado a {ruta.get_estado_display()} para la comisión {ruta.comision.nombre}.')
        else:
            messages.error(request, 'Estado no válido.')
    
    return redirect('proyectos:detalle_proyecto', pk=proyecto.pk)