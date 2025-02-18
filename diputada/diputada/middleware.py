from django.contrib import messages
from django.shortcuts import redirect

class SessionExpiryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.method == 'POST':
            # Método moderno para detectar peticiones AJAX
            if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                if not request.POST.get('csrfmiddlewaretoken'):
                    messages.error(request, 'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.')
                    return redirect('usuario:login')
        return self.get_response(request) 