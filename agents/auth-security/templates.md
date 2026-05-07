# Auth Security Templates

## Example 1: Role check
```python
def es_diputada(user):
    return user.is_authenticated and hasattr(user, 'perfil') and user.perfil.es_diputada
```

## Example 2: Protected view
```python
@login_required
def mis_proyectos(request):
    if not es_diputada(request.user):
        return redirect('index')
```

## Example 3: Security setting note
```text
Only expose DEBUG=True in local development; keep production hosts and CSRF origins explicit.
```