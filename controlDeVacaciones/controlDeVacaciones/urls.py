from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView 

from django.http import HttpResponse
from django.conf import settings
import os

def service_worker(request):
    """
    Serve the service worker creation from the root to allow global scope.
    """
    sw_path = os.path.join(settings.BASE_DIR, 'gestion', 'static', 'sw.js')
    try:
        with open(sw_path, 'r') as f:
            return HttpResponse(f.read(), content_type='application/javascript')
    except FileNotFoundError:
        return HttpResponse("Error: sw.js not found in static folder", status=404)

urlpatterns = [
    # 1. Administración de Django
    path('admin/', admin.site.urls),
    
    # PWA Service Worker (Root Scope)
    path('sw.js', service_worker, name='service_worker'),

    # 2. Login y Logout (Se corrige la ruta de la plantilla a 'gestion/login.html')
    # 🛑 CORRECCIÓN CLAVE: template_name='gestion/login.html'
    path('login/', auth_views.LoginView.as_view(template_name='gestion/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'), 
    
    # 3. Módulo principal de Gestión (Crucial: definir el namespace 'gestion')
    path('gestion/', include('gestion.urls', namespace='gestion')),
    
    # 4. Redirección de la raíz ('/') a la página de login por defecto
    path('', RedirectView.as_view(pattern_name='login', permanent=False), name='root_redirect'),
]