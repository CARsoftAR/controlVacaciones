from django.urls import path
from . import views
from . import backup_views
from django.contrib import admin
from django.urls import path, include

# Define el nombre de la aplicación (namespace) para poder usar 'gestion:nombre_ruta'
app_name = 'gestion' 

urlpatterns = [

    # --- Rutas de Uso General ---
    path('', views.dashboard, name='dashboard'),
    path('cambiar-password/', views.cambiar_password, name='cambiar_password'),
    path('solicitud/', views.solicitar_vacaciones, name='solicitar_vacaciones'),
    path('calendario_global/', views.calendario_global, name='calendario_global'),
    path('calendario_global/exportar/', views.exportar_calendario_excel, name='exportar_calendario_excel'),
    
    # --- Rutas de Empleado (Personal) ---
    path('dias_disponibles/', views.dias_disponibles_view, name='dias_disponibles'), 
    path('mis_vacaciones/solicitar/', views.solicitar_mis_vacaciones, name='solicitar_mis_vacaciones'),
    # Usando 'historial_personal' como nombre para la vista
    path('mi_historial/', views.mi_historial, name='historial_personal'), 
    
    path('mi_perfil/', views.mi_perfil, name='mi_perfil'),
  
    # 🌟 NUEVO: Ruta para exportar a .ics
    path('vacacion/<int:vacacion_id>/ics/', views.exportar_notificacion_vacaciones_ics, name='exportar_notificacion_ics'),

    # --- Rutas de Manager/Administración ---
    
    # 🌟 CRÍTICO: Ruta para la gestión de solicitudes por el manager
    path('aprobacion/manager/', views.aprobacion_manager, name='aprobacion_manager'),

    path('empleados/', views.gestion_empleados, name='gestion_empleados'),
    path('empleados/nuevo/', views.crear_empleado, name='crear_empleado'),
    path('empleados/<int:empleado_id>/editar/', views.editar_empleado, name='editar_empleado'),
    path('empleados/<int:empleado_id>/eliminar/', views.eliminar_empleado, name='eliminar_empleado'),
    path('historial_global/', views.historial_global, name='historial_global'),
    path('saldos/', views.gestion_saldos, name='gestion_saldos'),
    path('festivos/', views.gestion_festivos, name='gestion_festivos'),
    path('festivos/<int:festivo_id>/eliminar/', views.eliminar_festivo, name='eliminar_festivo'),
    path('calendario_manager/', views.calendario_manager, name='calendario_manager'),
    path('calendario_interactivo/', views.calendario_interactivo, name='calendario_interactivo'),
    path('api/vacaciones/listar/', views.api_vacaciones_listar, name='api_vacaciones_listar'),
    path('api/vacaciones/mover/', views.api_vacaciones_mover, name='api_vacaciones_mover'),
    path('configurar_email/', views.configurar_email, name='configurar_email'),
    path('probar_email/', views.probar_email, name='probar_email'),



    # --- Rutas de Utilidad (AJAX) ---
    path('saldo_ajax/', views.obtener_saldo_empleado, name='obtener_saldo_empleado'),
    path(
        'solicitud/<int:solicitud_id>/accion/', 
        views.aprobar_rechazar_solicitud, 
        name='aprobar_rechazar'
    ),
    
    # --- Exportación PDF ---
    path('notificacion-pdf/<int:empleado_id>/<int:vacacion_id>/', views.exportar_notificacion_vacaciones_pdf, name='exportar_notificacion_pdf'),
    

    # --- Sistema de Backup ---
    path('backup/', backup_views.backup_dashboard, name='backup_dashboard'),
    path('backup/db/crear/', backup_views.crear_backup_db, name='crear_backup_db'),
    path('backup/code/crear/', backup_views.crear_backup_code, name='crear_backup_code'),
    path('backup/github/crear/', backup_views.crear_backup_github, name='crear_backup_github'),
    path('backup/completo/crear/', backup_views.crear_backup_completo, name='crear_backup_completo'),
    path('backup/<int:backup_id>/descargar/', backup_views.descargar_backup, name='descargar_backup'),
    path('backup/<int:backup_id>/eliminar/', backup_views.eliminar_backup, name='eliminar_backup'),

    # --- Notificaciones ---
    path('notificaciones/', views.lista_notificaciones, name='lista_notificaciones'),
    path('notificaciones/marcar-leida/<int:notif_id>/', views.marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('api/check_notificaciones/', views.api_check_notificaciones, name='api_check_notificaciones'),
]