from django import template
from datetime import date

register = template.Library()

@register.filter
def esta_en_vacaciones(dia, vacaciones):
    """
    Verifica si un día específico está dentro de algún período de vacaciones.
    
    Args:
        dia: objeto date
        vacaciones: QuerySet de RegistroVacaciones
    
    Returns:
        True si el día está en vacaciones, False en caso contrario
    """
    if not isinstance(dia, date):
        return False
    
    for vacacion in vacaciones:
        if vacacion.fecha_inicio <= dia <= vacacion.fecha_fin:
            return True
    return False

@register.filter
def semana_tiene_vacaciones(dias_semana, vacaciones):
    """
    Verifica si alguno de los días de la semana está en vacaciones.
    """
    if not dias_semana:
        return False
        
    for dia in dias_semana:
        for vacacion in vacaciones:
            if vacacion.fecha_inicio <= dia <= vacacion.fecha_fin:
                return True
    return False

@register.filter
def get_vacacion_semana(dias_semana, vacaciones):
    """
    Retorna el OBJETO de vacación que coincide con esta semana.
    Prioriza Aprobada sobre Pendiente.
    """
    if not dias_semana:
        return None
        
    # Primera pasada: Buscar Aprobadas
    for dia in dias_semana:
        for vacacion in vacaciones:
            if vacacion.fecha_inicio <= dia <= vacacion.fecha_fin:
                if vacacion.estado == 'Aprobada':
                    return vacacion

    # Segunda pasada: Buscar Pendientes
    for dia in dias_semana:
        for vacacion in vacaciones:
            if vacacion.fecha_inicio <= dia <= vacacion.fecha_fin:
                 if vacacion.estado == 'Pendiente':
                    return vacacion
                    
    return None

@register.filter
def estado_vacacion_semana(dias_semana, vacaciones):
    """
    Retorna el estado de la vacación para una semana específica.
    Retorna 'aprobada', 'pendiente', o None si no hay vacaciones.
    """
    if not dias_semana:
        return None
        
    for dia in dias_semana:
        for vacacion in vacaciones:
            if vacacion.fecha_inicio <= dia <= vacacion.fecha_fin:
                # Retornar el primer estado encontrado
                if vacacion.estado == 'Aprobada':
                    return 'aprobada'
                elif vacacion.estado == 'Pendiente':
                    return 'pendiente'
    return None

@register.filter
def dias_vacacion_semana(dias_semana, vacaciones):
    """
    Cuenta cuántos días de la semana están cubiertos por vacaciones.
    """
    if not dias_semana:
        return 0
    
    count = 0
    for dia in dias_semana:
        for vacacion in vacaciones:
            if vacacion.fecha_inicio <= dia <= vacacion.fecha_fin:
                count += 1
                break
    return count
