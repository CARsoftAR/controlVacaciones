from .models import Notificacion, RegistroVacaciones

def notificaciones_context(request):
    if request.user.is_authenticated:
        # Notificaciones de sistema
        notif_qs = request.user.notificaciones.filter(leida=False)
        notif_count = notif_qs.count()
        
        # Tareas pendientes (solo para managers)
        tareas_pendientes = 0
        if hasattr(request.user, 'empleado') and request.user.empleado.es_manager:
            from django.db.models import Q
            # Si es superusuario (Administrador), ve TODAS las solicitudes pendientes de la empresa
            if request.user.is_superuser:
                filter_q = Q() 
            else:
                # Si no es superusuario, SOLO ve las que tiene asignadas directamente a él
                filter_q = Q(manager_aprobador=request.user.empleado)
                
            tareas_pendientes = RegistroVacaciones.objects.filter(
                filter_q,
                estado=RegistroVacaciones.ESTADO_PENDIENTE
            ).count()

        # Traer las últimas 5 para el dropdown rápido
        ultimas_notif = notif_qs[:5]
        
        # ID de la última notificación para el polling
        last_notif = request.user.notificaciones.order_by('-id').first()
        notif_last_id = last_notif.id if last_notif else 0
        
        return {
            'notif_count': notif_count + tareas_pendientes,
            'notif_list_preview': ultimas_notif,
            'tareas_pendientes_count': tareas_pendientes,
            'notif_last_id': notif_last_id
        }
    return {
        'notif_count': 0,
        'notif_list_preview': [],
        'tareas_pendientes_count': 0
    }

