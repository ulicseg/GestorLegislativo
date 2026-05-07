# Frontend Templates

## Example 1: Template with errors and actions
```html
{% extends 'base.html' %}
{% block content %}
<main class="container py-4">
  <h1 class="mb-3">Crear proyecto</h1>
  <form method="post" novalidate>
    {% csrf_token %}
    {{ form.non_field_errors }}
    {{ form.as_p }}
    <button type="submit" class="btn btn-primary">Guardar</button>
  </form>
</main>
{% endblock %}
```

## Example 2: Reusable include
```html
<div class="alert alert-info" role="status">
  {{ message }}
</div>
```

## Example 3: Small progressive enhancement
```javascript
document.querySelectorAll('[data-copy]').forEach((button) => {
  button.addEventListener('click', () => {
    navigator.clipboard.writeText(button.dataset.copy);
  });
});
```