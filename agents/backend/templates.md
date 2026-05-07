# Backend Templates

## Example 1: View with validation
```python
from django.contrib import messages
from django.shortcuts import redirect, render

def crear_proyecto(request):
    if request.method == 'POST':
        form = ProyectoForm(request.POST)
        if form.is_valid():
            proyecto = form.save(commit=False)
            proyecto.creado_por = request.user
            proyecto.save()
            messages.success(request, 'Proyecto creado correctamente.')
            return redirect('proyectos:detalle', pk=proyecto.pk)
    else:
        form = ProyectoForm()

    return render(request, 'proyectos/crear_proyecto.html', {'form': form})
```

## Example 2: Shared business helper
```python
def normalizar_numero_proyecto(numero):
    numero = numero.strip()
    if '/' not in numero:
        raise ValidationError('El numero debe tener formato XXXX/XX')
    return numero.upper()
```

## Example 3: Transactional update
```python
from django.db import transaction

@transaction.atomic
def cambiar_estado(proyecto, nuevo_estado):
    ruta = proyecto.ruta_comisiones.select_for_update().first()
    ruta.estado = nuevo_estado
    ruta.save(update_fields=['estado'])
```