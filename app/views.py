import logging

from django.db import connection
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views


class CustomLoginView(auth_views.LoginView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/')  # Redireciona para a URL de contratos
        return super().dispatch(request, *args, **kwargs)
    


def custom_404(request, exception):
    return render(request, '404.html', status=404)


def health(request):
    """Healthcheck do container: 200 só se o banco responde."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        logging.getLogger(__name__).exception("health: banco inacessível")
        return HttpResponse("db error", status=503, content_type="text/plain")
    return HttpResponse("ok", content_type="text/plain")
