import logging
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Empleado, ConfiguracionEmail, Notificacion

logger = logging.getLogger(__name__)

def crear_notificacion(usuario, titulo, mensaje, url=None, solicitud=None):
    """Crea una notificación interna para un usuario."""
    try:
        Notificacion.objects.create(
            usuario=usuario,
            titulo=titulo,
            mensaje=mensaje,
            url=url,
            solicitud=solicitud
        )
    except Exception as e:

        logger.error(f"Error al crear notificación: {e}")


def _get_email_config():
    """Retorna la configuración activa de la base de datos o None."""
    try:
        return ConfiguracionEmail.objects.filter(activo=True).first()
    except:
        return None

def _enviar_email_generico(request, subject, context, template_name, destinatarios, force_config=None):
    """
    Función interna para manejar la lógica de envío usando la configuración de la DB o settings.py.
    """
    try:
        # Usar config forzada (test) o la de la DB activa
        config = force_config if force_config else _get_email_config()
        
        # 1. Determinar el servidor (Connection)
        connection = None
        from_email = settings.DEFAULT_FROM_EMAIL
        
        if config:
            connection = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host=config.email_host,
                port=config.email_port,
                username=config.email_host_user,
                password=config.email_host_password,
                use_tls=config.email_use_tls,
                use_ssl=config.email_use_ssl,
            )
            from_email = config.email_host_user



        # 2. Configurar el sitio URL
        protocol = 'https' if request.is_secure() else 'http'
        domain = get_current_site(request).domain
        context['site_url'] = f"{protocol}://{domain}"

        # 3. Renderizar contenido
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)

        # 4. Enviar
        email = EmailMultiAlternatives(
            subject,
            text_content,
            from_email,
            destinatarios,
            connection=connection
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True

    except Exception as e:
        logger.error(f"Error en _enviar_email_generico: {e}")
        # Retornar el string del error para poder mostrarlo en el test
        raise e

def probar_configuracion_email(request, config):
    """
    Intenta enviar un email de prueba y retorna (Success, ErrorMessage)
    """
    try:
        subject = "Prueba de Conexion - Sistema de Vacaciones"

        context = {
            'mensaje': 'Si estás leyendo esto, la configuración de tu servidor de correo es CORRECTA.',
            'timestamp': timezone.now()
        }
        # Obtener destinatarios de la lista de alertas
        destinatarios_test = []
        if config.emails_notificacion:
            # Limpiar espacios y filtrar vacíos
            extras = [e.strip() for e in config.emails_notificacion.split(',') if e.strip()]
            destinatarios_test.extend(extras)
        
        # Agregar al usuario actual si no está
        if request.user.email and request.user.email.strip() not in destinatarios_test:
            destinatarios_test.append(request.user.email.strip())
            
        # Si sigue vacío, usar la propia cuenta que envía
        if not destinatarios_test:
            destinatarios_test.append(config.email_host_user)

        # Intentar envío FORZANDO la configuración
        success = _enviar_email_generico(
            request, 
            subject, 
            context, 
            'gestion/emails/test_email.html', 
            destinatarios_test,
            force_config=config
        )
        
        if success:
            return True, f"Email enviado con éxito a: {', '.join(destinatarios_test)}. Revisa las bandejas de entrada."

        else:
            return False, "El servidor rechazó el envío."

            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error en prueba de email: {error_msg}")
        return False, error_msg

def enviar_email_nueva_solicitud(request, solicitud):
    """
    Notifica sobre una nueva solicitud. 
    """
    try:
        managers = Empleado.objects.filter(es_manager=True).exclude(user__email='')
        destinatarios = [m.user.email for m in managers]
        
        config = _get_email_config()
        if config and config.emails_notificacion:
            extras = [e.strip() for e in config.emails_notificacion.split(',') if e.strip()]
            destinatarios.extend(extras)
            
        destinatarios = list(set([d for d in destinatarios if d]))
        
        if not destinatarios:
            return False

        # Obtener saldo para el periodo
        ciclo = solicitud.fecha_inicio.year
        saldo = solicitud.empleado.saldovacaciones_set.filter(ciclo=ciclo).first()
        restan = saldo.total_disponible() if saldo else "N/A"

        subject = f"🔔 Nueva Solicitud: {solicitud.empleado.nombre} {solicitud.empleado.apellido}"
        context = {
            'solicitud': solicitud,
            'ciclo': ciclo,
            'restan': restan
        }
        
        return _enviar_email_generico(
            request, subject, context, 
            'gestion/emails/notificacion_solicitud.html', 
            destinatarios
        )
    except Exception as e:
        logger.error(f"Error enviando email nueva solicitud: {e}")
        return False

def enviar_email_cambio_estado(request, solicitud):
    """
    Notifica al empleado sobre el cambio de su solicitud.
    """
    try:
        if not solicitud.empleado.user or not solicitud.empleado.user.email:
            return False

        # Obtener saldo para el periodo
        ciclo = solicitud.fecha_inicio.year
        saldo = solicitud.empleado.saldovacaciones_set.filter(ciclo=ciclo).first()
        restan = saldo.total_disponible() if saldo else "N/A"

        destinatario = [solicitud.empleado.user.email]
        subject = f"📢 Solicitud de Vacaciones {solicitud.estado.upper()}"
        context = {
            'solicitud': solicitud,
            'ciclo': ciclo,
            'restan': restan
        }
        
        return _enviar_email_generico(
            request, subject, context, 
            'gestion/emails/cambio_estado_solicitud.html', 
            destinatario
        )
    except Exception as e:
        logger.error(f"Error enviando email cambio estado: {e}")
        return False

