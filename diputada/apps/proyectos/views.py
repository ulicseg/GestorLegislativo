from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Proyecto, Actualizacion, Temario, ProyectoTemario, Categoria, RutaComision
from .forms import ProyectoForm, ActualizacionForm, ProyectoFilterForm, TemarioForm, TemarioFilterForm
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.db import models, transaction, IntegrityError
from apps.usuario.views import es_diputada
import json
import re
from django.http import HttpResponse, JsonResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.units import inch
from io import BytesIO
from django.urls import reverse
from bs4 import BeautifulSoup, NavigableString
import html # Importar el módulo html

def limpiar_html(html_content):
    """Mantiene formato básico compatible con Paragraph de ReportLab."""
    if not html_content:
        return ""

    try:
        soup = BeautifulSoup(html.unescape(str(html_content)), 'html.parser')
        root = soup.body if soup.body else soup

        partes = []
        for child in root.children:
            partes.append(_nodo_a_markup_reportlab(child))

        markup = ''.join(partes)
        markup = re.sub(r'(<br/>\s*){3,}', '<br/><br/>', markup).strip()
        return markup or html.escape(root.get_text(' ', strip=True))
    except Exception as e:
        print(f"ERROR en limpiar_html procesando contenido: {str(e)}. Contenido original: {str(html_content)[:200]}...")
        return html.escape(str(html_content)) if html_content else ""


def _extraer_alineacion(style_str):
    if not style_str:
        return None
    match = re.search(r'text-align\s*:\s*(left|right|center|justify)', style_str.lower())
    return match.group(1) if match else None


def _nodo_a_markup_reportlab(node):
    if isinstance(node, NavigableString):
        return html.escape(str(node))

    if not getattr(node, 'name', None):
        return ''

    tag = node.name.lower()

    if tag == 'br':
        return '<br/>'

    hijos = ''.join(_nodo_a_markup_reportlab(child) for child in node.children)

    if tag in ['b', 'strong']:
        return f'<b>{hijos}</b>'
    if tag in ['i', 'em']:
        return f'<i>{hijos}</i>'
    if tag == 'u':
        return f'<u>{hijos}</u>'

    if tag in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']:
        if tag == 'li':
            hijos = f'• {hijos}'
        return f'{hijos}<br/>'

    return hijos


def _estilo_con_alineacion(base_style, alineacion):
    estilo = ParagraphStyle(f'{base_style.name}_{alineacion}', parent=base_style)
    mapping = {
        'left': TA_LEFT,
        'center': TA_CENTER,
        'right': TA_RIGHT,
        'justify': TA_JUSTIFY,
    }
    estilo.alignment = mapping.get(alineacion, base_style.alignment)
    return estilo


def _agregar_parrafo_seguro(flowables, markup, estilo):
    """Agrega Paragraph evitando que un markup inválido rompa la generación completa."""
    if not markup:
        return

    try:
        flowables.append(Paragraph(markup, estilo))
    except Exception:
        texto_plano = BeautifulSoup(markup, 'html.parser').get_text(' ', strip=True)
        if texto_plano:
            flowables.append(Paragraph(html.escape(texto_plano), estilo))


def agregar_html_a_elementos(flowables, html_content, base_style, spacer_height=6):
    """Convierte HTML rico a párrafos seguros preservando negrita y alineación."""
    if not html_content:
        return

    soup = BeautifulSoup(html.unescape(str(html_content)), 'html.parser')
    root = soup.body if soup.body else soup
    buffer_inline = []
    hay_contenido = False

    def volcar_buffer_con_estilo(estilo_destino):
        nonlocal buffer_inline, hay_contenido
        if not buffer_inline:
            return
        markup_inline = ''.join(buffer_inline).strip()
        if markup_inline:
            _agregar_parrafo_seguro(flowables, markup_inline, estilo_destino)
            hay_contenido = True
        buffer_inline = []

    for child in root.children:
        if isinstance(child, NavigableString):
            texto = html.escape(str(child))
            if texto.strip():
                buffer_inline.append(texto)
            continue

        if not getattr(child, 'name', None):
            continue

        tag = child.name.lower()
        es_bloque = tag in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']

        if es_bloque:
            alineacion = _extraer_alineacion(child.get('style', ''))
            estilo_bloque = _estilo_con_alineacion(base_style, alineacion) if alineacion else base_style

            volcar_buffer_con_estilo(base_style)

            markup = ''.join(_nodo_a_markup_reportlab(n) for n in child.children).strip()
            if tag == 'li' and markup:
                markup = f'• {markup}'

            if markup:
                _agregar_parrafo_seguro(flowables, markup, estilo_bloque)
                hay_contenido = True
            continue

        buffer_inline.append(_nodo_a_markup_reportlab(child))

    volcar_buffer_con_estilo(base_style)

    if not hay_contenido:
        markup = limpiar_html(html_content)
        if markup:
            _agregar_parrafo_seguro(flowables, markup, base_style)
            hay_contenido = True

    if spacer_height and hay_contenido:
        flowables.append(Spacer(1, spacer_height))

def limpiar_html_para_item(item_html_content):
    """Función auxiliar para limpiar el contenido de un item de lista, preservando b, i, u."""
    if not item_html_content:
        return ""
    soup = BeautifulSoup(item_html_content, 'html.parser')
    for tag in soup.find_all(True):
        if tag.name in ['b', 'i', 'u']:
            tag.attrs = {}
        elif tag.name not in ['html', 'body']: # Evitar desenvolver el fragmento en sí
            tag.unwrap()

    if soup.body:
        return soup.body.encode_contents(formatter="html").decode('utf-8').strip()
    else:
        return soup.encode_contents(formatter="html").decode('utf-8').strip()


def _normalizar_proyectos_temario(proyectos_data):
    """Normaliza proyectos y garantiza orden único secuencial para evitar colisiones."""
    if not isinstance(proyectos_data, list):
        return []

    items = []
    for idx, item in enumerate(proyectos_data):
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            continue

        proyecto_id, datos = item
        try:
            proyecto_id = int(proyecto_id)
        except (TypeError, ValueError):
            continue

        orden = 0
        if isinstance(datos, dict):
            try:
                orden = int(datos.get('orden', 0))
            except (TypeError, ValueError):
                orden = 0

        items.append((idx, proyecto_id, orden))

    # Respeta orden declarado y, ante empate, el orden de llegada.
    items.sort(key=lambda x: (x[2], x[0]))

    # Evita proyectos duplicados.
    vistos = set()
    proyecto_ids = []
    for _, proyecto_id, _ in items:
        if proyecto_id in vistos:
            continue
        vistos.add(proyecto_id)
        proyecto_ids.append(proyecto_id)

    return [(proyecto_id, orden_idx) for orden_idx, proyecto_id in enumerate(proyecto_ids, start=1)]

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
        solo_proyectos_diputada = filter_form.cleaned_data.get('solo_proyectos_diputada')

        if busqueda:
            proyectos_list = proyectos_list.filter(titulo__icontains=busqueda)

        if numero:
            proyectos_list = proyectos_list.filter(numero__icontains=numero)

        if categoria:
            proyectos_list = proyectos_list.filter(categoria=categoria)

        if solo_proyectos_diputada:
            proyectos_list = proyectos_list.filter(es_proyecto_diputada=True)

    # Ordenar proyectos por fecha de creación
    proyectos_list = proyectos_list.order_by('-fecha_creacion')

    # Paginación
    paginator = Paginator(proyectos_list, 10)
    page = request.GET.get('page')
    proyectos = paginator.get_page(page)
    
    # Calcular rango de páginas para paginación compacta
    page_range = []
    current_page = proyectos.number
    total_pages = paginator.num_pages
    
    # Siempre mostrar la primera página
    if total_pages > 0:
        page_range.append(1)
    
    # Agregar puntos suspensivos si es necesario después de la primera página
    if current_page > 4:
        page_range.append('...')
    
    # Agregar páginas cercanas a la actual
    start_range = max(2, current_page - 2)
    end_range = min(total_pages, current_page + 2)
    
    for i in range(start_range, end_range + 1):
        if i != 1 and i != total_pages:  # No duplicar primera y última
            page_range.append(i)
    
    # Agregar puntos suspensivos si es necesario antes de la última página
    if current_page < total_pages - 3:
        page_range.append('...')
    
    # Siempre mostrar la última página (si no es la primera)
    if total_pages > 1:
        page_range.append(total_pages)

    context = {
        'proyectos': proyectos,
        'es_diputada': request.user.perfil.es_diputada,
        'filter_form': filter_form,
        'page_range': page_range
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
            
            # Si es AJAX, devolver JSON con el HTML de la nueva actualización
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.template.loader import render_to_string
                # Obtener temario_id si se proporciona
                temario_id = request.POST.get('temario_id')
                html = render_to_string('proyectos/partials/actualizacion_item.html', {
                    'actualizacion': actualizacion,
                    'user': request.user,
                    'temario_id': temario_id
                })
                return JsonResponse({
                    'success': True,
                    'message': 'Actualización agregada exitosamente.',
                    'html': html,
                    'actualizacion_id': actualizacion.pk
                })
            
            messages.success(request, 'Actualización agregada exitosamente.')
            # Para requests tradicionales, redirigir
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return redirect(referer)
            return redirect('proyectos:detalle_proyecto', pk=proyecto.pk)
        
        # Si es AJAX, devolver error como JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Error al agregar la actualización.',
                'errors': form.errors
            }, status=400)

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
    from_temario = request.GET.get('from') == 'temario'
    temario_id = request.GET.get('temario_id')

    # Verificar que el usuario sea el autor de la actualización o sea diputada
    if request.user == actualizacion.autor or request.user.perfil.es_diputada:
        if request.method == 'POST':
            actualizacion.delete()
            
            # Detectar si es AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Actualización eliminada exitosamente.'
                })
            
            messages.success(request, 'Actualización eliminada exitosamente.')
    else:
        # Detectar si es AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'No tienes permiso para eliminar esta actualización.'
            }, status=403)
        
        messages.error(request, 'No tienes permiso para eliminar esta actualización.')

    # Si viene del temario, redirigir al temario
    if from_temario and temario_id:
        return redirect('proyectos:detalle_temario', pk=temario_id)
    
    # Si no, redirigir al proyecto
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
    temarios_list = Temario.objects.select_related('comision').prefetch_related('proyectotemario_set__proyecto').order_by('-fecha_creacion')

    filter_form = TemarioFilterForm(request.GET)
    if filter_form.is_valid():
        numero = filter_form.cleaned_data.get('numero')
        categoria = filter_form.cleaned_data.get('categoria')

        if numero:
            temarios_list = temarios_list.filter(numero=numero)
        if categoria:
            temarios_list = temarios_list.filter(comision=categoria)

    # Paginación
    paginator = Paginator(temarios_list, 10)
    page = request.GET.get('page')
    temarios = paginator.get_page(page)
    
    # Calcular rango de páginas para paginación compacta
    page_range = []
    current_page = temarios.number
    total_pages = paginator.num_pages
    
    # Siempre mostrar la primera página
    if total_pages > 0:
        page_range.append(1)
    
    # Agregar puntos suspensivos si es necesario después de la primera página
    if current_page > 4:
        page_range.append('...')
    
    # Agregar páginas cercanas a la actual
    start_range = max(2, current_page - 2)
    end_range = min(total_pages, current_page + 2)
    
    for i in range(start_range, end_range + 1):
        if i != 1 and i != total_pages:  # No duplicar primera y última
            page_range.append(i)
    
    # Agregar puntos suspensivos si es necesario antes de la última página
    if current_page < total_pages - 3:
        page_range.append('...')
    
    # Siempre mostrar la última página (si no es la primera)
    if total_pages > 1:
        page_range.append(total_pages)

    return render(request, 'proyectos/listar_temarios.html', {
        'temarios': temarios,
        'filter_form': filter_form,
        'page_range': page_range
    })

@login_required
def crear_temario(request):
    if request.method == 'POST':
        form = TemarioForm(request.POST)
        if form.is_valid():
            try:
                proyectos_data = json.loads(request.POST.get('proyectos', '[]'))
                proyectos_normalizados = _normalizar_proyectos_temario(proyectos_data)

                with transaction.atomic():
                    temario = form.save()
                    for proyecto_id, orden in proyectos_normalizados:
                        ProyectoTemario.objects.create(
                            temario=temario,
                            proyecto_id=proyecto_id,
                            orden=orden
                        )

                messages.success(request, 'Temario creado exitosamente.')
                return redirect('proyectos:listar_temarios')
            except (json.JSONDecodeError, IntegrityError, ValueError, TypeError):
                messages.error(request, 'No se pudo guardar el temario: revise el orden y los proyectos seleccionados.')
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
            try:
                proyectos_data = json.loads(request.POST.get('proyectos', '[]'))
                proyectos_normalizados = _normalizar_proyectos_temario(proyectos_data)

                with transaction.atomic():
                    temario = form.save()

                    # Eliminar relaciones existentes
                    ProyectoTemario.objects.filter(temario=temario).delete()

                    # Crear nuevas relaciones con orden secuencial único
                    for proyecto_id, orden in proyectos_normalizados:
                        ProyectoTemario.objects.create(
                            temario=temario,
                            proyecto_id=proyecto_id,
                            orden=orden
                        )

                messages.success(request, 'Temario actualizado exitosamente.')
                return redirect('proyectos:listar_temarios')
            except (json.JSONDecodeError, IntegrityError, ValueError, TypeError):
                messages.error(request, 'No se pudo actualizar el temario: revise el orden y los proyectos seleccionados.')
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
    form = ActualizacionForm()  # Crear una instancia del formulario

    return render(request, 'proyectos/detalle_temario.html', {
        'temario': temario,
        'proyectos_temario': proyectos_temario,
        'form': form  # Pasar el formulario al contexto
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
    # Mostrar a todos solo proyectos marcados como de la diputada
    proyectos = Proyecto.objects.filter(
        es_proyecto_diputada=True
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
        try:
            descripcion_original = pt.proyecto.descripcion # Guardar original para logging
            agregar_html_a_elementos(elements, descripcion_original, content_style, spacer_height=6)
        except ValueError as e: # Específicamente para errores de parseo de ReportLab
            print(f"ERROR_PDF_GENERATION: ReportLab ValueError para Proyecto ID {pt.proyecto.id} (Temario ID {temario.pk}).")
            print(f"ERROR_PDF_GENERATION: Mensaje de error: {str(e)}")
            print(f"ERROR_PDF_GENERATION: Descripcion Original (antes de limpiar_html):\n'''{descripcion_original}\'''")
            # Fallback: usar texto plano si reportlab falla con el HTML limpio
            texto_plano = BeautifulSoup(descripcion_original, 'html.parser').get_text() if descripcion_original else "Sin descripción disponible"
            elements.append(Paragraph(texto_plano, content_style))
            messages.warning(request, f"Advertencia: Se usó texto plano para la descripción del proyecto {pt.proyecto.numero} ({pt.proyecto.titulo}) debido a un problema de formato HTML.")
        except Exception as e: # Capturar cualquier otra excepción durante la limpieza o el append
            print(f"ERROR_PDF_GENERATION: Excepción general al procesar descripción del Proyecto ID {pt.proyecto.id} (Temario ID {temario.pk}).")
            print(f"ERROR_PDF_GENERATION: Mensaje de error: {str(e)}")
            descripcion_original = pt.proyecto.descripcion # Asegurarse de que está definida para el log
            print(f"ERROR_PDF_GENERATION: Descripcion Original (si disponible):\n'''{descripcion_original}\'''")
            # Fallback: usar texto plano
            texto_plano = BeautifulSoup(descripcion_original, 'html.parser').get_text() if descripcion_original else "Sin descripción disponible"
            elements.append(Paragraph(texto_plano, content_style))
            messages.error(request, f"Error crítico al procesar la descripción del proyecto {pt.proyecto.numero} ({pt.proyecto.titulo}). Se usó texto plano.")

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
                try:
                    contenido_original_actualizacion = actualizacion.contenido # Guardar original
                    agregar_html_a_elementos(elements, contenido_original_actualizacion, update_style, spacer_height=0)
                except ValueError as e: # Específicamente para errores de parseo de ReportLab
                    print(f"ERROR_PDF_GENERATION: ReportLab ValueError para Actualizacion ID {actualizacion.id} (Proyecto ID {pt.proyecto.id}, Temario ID {temario.pk}).")
                    print(f"ERROR_PDF_GENERATION: Mensaje de error: {str(e)}")
                    print(f"ERROR_PDF_GENERATION: Contenido Original Actualizacion:\n'''{contenido_original_actualizacion}\'''")
                    texto_plano_actualizacion = BeautifulSoup(contenido_original_actualizacion, 'html.parser').get_text() if contenido_original_actualizacion else "Sin contenido"
                    elements.append(Paragraph(texto_plano_actualizacion, update_style))
                    messages.warning(request, f"Advertencia: Se usó texto plano para una actualización del proyecto {pt.proyecto.numero} ({pt.proyecto.titulo}) debido a un problema de formato HTML.")
                except Exception as e: # Capturar cualquier otra excepción
                    print(f"ERROR_PDF_GENERATION: Excepción general al procesar Actualizacion ID {actualizacion.id} (Proyecto ID {pt.proyecto.id}, Temario ID {temario.pk}).")
                    print(f"ERROR_PDF_GENERATION: Mensaje de error: {str(e)}")
                    contenido_original_actualizacion = actualizacion.contenido # Asegurarse para el log
                    print(f"ERROR_PDF_GENERATION: Contenido Original Actualizacion (si disponible):\n'''{contenido_original_actualizacion}\'''")
                    # En caso de error, mostrar texto plano
                    texto_plano_actualizacion = BeautifulSoup(contenido_original_actualizacion, 'html.parser').get_text() if contenido_original_actualizacion else "Sin contenido"
                    elements.append(Paragraph(
                        texto_plano_actualizacion,
                        update_style
                    ))
                    messages.error(request, f"Error crítico al procesar una actualización del proyecto {pt.proyecto.numero} ({pt.proyecto.titulo}). Se usó texto plano.")

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
def descargar_proyecto_pdf(request, proyecto_pk, temario_pk):
    """
    Genera un PDF con la información de un proyecto específico dentro de un temario.
    """
    proyecto = get_object_or_404(Proyecto, pk=proyecto_pk)
    temario = get_object_or_404(Temario, pk=temario_pk)

    # Verificar que el proyecto pertenece al temario
    if not ProyectoTemario.objects.filter(proyecto=proyecto, temario=temario).exists():
        messages.error(request, 'El proyecto no pertenece al temario especificado.')
        return redirect('proyectos:detalle_temario', pk=temario_pk)

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

    # Definir todos los estilos necesarios (igual que en descargar_temario_pdf)
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
    fecha = proyecto.fecha_creacion
    fecha_esp = f"{fecha.day} de {meses[fecha.month - 1]} de {fecha.year}"

    # Encabezado y título
    elements.append(Paragraph("Sistema de Proyectos Legislativos", header_style))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"{proyecto.get_tipo_display()} {proyecto.numero}", title_style))
    elements.append(Paragraph(f"{proyecto.titulo}", heading_style))
    elements.append(Paragraph(f"Comisión: {temario.comision.nombre} - Temario #{temario.numero}", meta_style))
    elements.append(Paragraph(f"Creado el {fecha_esp} por {proyecto.creado_por.get_full_name()}", meta_style))
    elements.append(Spacer(1, 20))

    # Descripción del proyecto (limpiada)
    agregar_html_a_elementos(elements, proyecto.descripcion, content_style, spacer_height=0)

    # Ruta de comisiones
    rutas = proyecto.ruta_comisiones.all().order_by('orden')
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

    # Actualizaciones del proyecto
    if proyecto.actualizaciones.exists():
        elements.append(Paragraph("Historial de Actualizaciones:", heading_style))

        for actualizacion in proyecto.actualizaciones.all():
            fecha_act = actualizacion.fecha
            fecha_act_esp = f"{fecha_act.day} de {meses[fecha_act.month - 1]}"

            # Limpiar el contenido de la actualización
            agregar_html_a_elementos(elements, actualizacion.contenido, update_style, spacer_height=0)

            elements.append(Paragraph(
                f"Por: {actualizacion.autor.get_full_name()} - {fecha_act_esp}",
                author_style
            ))
            elements.append(Spacer(1, 10))

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
        return redirect('proyectos:detalle_temario', pk=temario_pk)

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f'{proyecto.get_tipo_display()}_{proyecto.numero}_{temario.comision.nombre}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response

@login_required
def descargar_proyecto_solo_pdf(request, proyecto_pk):
    proyecto = get_object_or_404(Proyecto, pk=proyecto_pk)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=inch,
                            leftMargin=inch,
                            topMargin=inch,
                            bottomMargin=inch)
    styles = getSampleStyleSheet()
    story = []

    # Estilo para el título del proyecto
    titulo_style = ParagraphStyle(
        'ProyectoTitulo',
        parent=styles['h1'],
        fontSize=18,
        leading=22,
        spaceAfter=0.2*inch,
        alignment=1 # Centrado
    )
    story.append(Paragraph(f"{proyecto.get_tipo_display()} {proyecto.numero}", titulo_style))
    story.append(Paragraph(proyecto.titulo, styles['h2']))
    story.append(Spacer(1, 0.2*inch))

    # Información meta
    meta_style = styles['Normal']
    meta_style.fontSize = 9
    meta_style.textColor = colors.grey
    story.append(Paragraph(f"Creado el {proyecto.fecha_creacion.strftime('%d/%m/%Y')} por {proyecto.creado_por.get_full_name()}", meta_style))
    story.append(Spacer(1, 0.3*inch))

    # Descripción del proyecto
    story.append(Paragraph("Descripción del Proyecto", styles['h3']))
    descripcion_style = ParagraphStyle('ProjectDescriptionStyle', parent=styles['Normal'], alignment=TA_JUSTIFY, leading=14)
    agregar_html_a_elementos(story, proyecto.descripcion, descripcion_style, spacer_height=0)
    story.append(Spacer(1, 0.2*inch))

    # Ruta de comisiones
    if proyecto.ruta_comisiones.exists():
        story.append(Paragraph("Ruta de Comisiones", styles['h3']))
        for ruta in proyecto.ruta_comisiones.all().order_by('orden'):
            story.append(Paragraph(f"{ruta.orden}. {ruta.comision.nombre} ({ruta.get_estado_display()})", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))

    # Actualizaciones
    if proyecto.actualizaciones.exists():
        story.append(Paragraph("Últimas Actualizaciones", styles['h3']))
        update_style = ParagraphStyle('ProjectUpdateStyle', parent=styles['Normal'], alignment=TA_JUSTIFY, leading=13)
        for actualizacion in proyecto.actualizaciones.all().order_by('-fecha'):
            story.append(Paragraph(f"{actualizacion.autor.get_full_name()} - {actualizacion.fecha.strftime('%d/%m/%Y %H:%M')}", meta_style))
            agregar_html_a_elementos(story, actualizacion.contenido, update_style, spacer_height=0)
            story.append(Spacer(1, 0.1*inch))
    else:
        story.append(Paragraph("No hay actualizaciones registradas", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="proyecto_{proyecto.numero}.pdf"'
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