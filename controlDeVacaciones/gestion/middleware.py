from django.shortcuts import redirect
from django.urls import reverse

class PrimerLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Verificar si tiene perfil de empleado y el flag activo
            if hasattr(request.user, 'empleado') and request.user.empleado.primer_login:
                
                # Lista de rutas permitidas (Login, Logout, Cambiar Password, Admin)
                # Es importante permitir logout para que no queden atrapados
                allowed_paths = [
                    reverse('gestion:cambiar_password'),
                    reverse('logout'),
                    reverse('login'), # Por seguridad
                ]
                
                # Permitir admin panel si es staff, por seguridad/mantenimiento
                if request.path.startswith('/admin/'):
                    return self.get_response(request)

                if request.path not in allowed_paths:
                    return redirect('gestion:cambiar_password')
        
        response = self.get_response(request)
        return response
