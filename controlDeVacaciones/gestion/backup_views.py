# gestion/backup_views.py

import os
import subprocess
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse, FileResponse, Http404
from django.core.management import call_command
from io import StringIO
from .models import Backup


def es_superusuario(user):
    """Verifica que el usuario sea superusuario"""
    return user.is_superuser


@login_required
@user_passes_test(es_superusuario)
def backup_dashboard(request):
    """Vista principal del sistema de backups"""
    backups = Backup.objects.all()[:20]  # Últimos 20 backups
    
    context = {
        'backups': backups,
        'titulo': 'Sistema de Backup y Restauración'
    }
    return render(request, 'gestion/backup_dashboard.html', context)


@login_required
@user_passes_test(es_superusuario)
def crear_backup_db(request):
    """Crea un backup de la base de datos"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Crear registro de backup
    backup = Backup.objects.create(
        tipo='db',
        usuario=request.user,
        status='processing'
    )
    
    try:
        # Configuración de la base de datos
        db_config = settings.DATABASES['default']
        db_name = db_config['NAME']
        db_user = db_config['USER']
        db_password = db_config['PASSWORD']
        db_host = db_config['HOST']
        db_port = db_config['PORT']

        # Crear directorio de backups si no existe
        output_dir = os.path.join(settings.BASE_DIR, 'backups', 'db')
        os.makedirs(output_dir, exist_ok=True)

        # Nombre del archivo de backup con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(output_dir, f'backup_{db_name}_{timestamp}.sql')

        # Comando mysqldump
        dump_cmd = [
            'mysqldump',
            f'--host={db_host}',
            f'--port={db_port}',
            f'--user={db_user}',
            f'--password={db_password}',
            '--single-transaction',
            '--routines',
            '--triggers',
            '--events',
            db_name
        ]

        # Ejecutar mysqldump
        with open(backup_file, 'w', encoding='utf-8') as f:
            result = subprocess.run(
                dump_cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )

        # Obtener tamaño del archivo
        file_size = os.path.getsize(backup_file)

        # Actualizar registro
        backup.archivo = backup_file
        backup.tamaño = file_size
        backup.status = 'completed'
        backup.save()

        messages.success(
            request,
            f'✅ Backup de base de datos creado exitosamente ({backup.tamaño_mb} MB)'
        )
        
        return JsonResponse({
            'success': True,
            'backup_id': backup.id,
            'archivo': backup_file,
            'tamaño_mb': backup.tamaño_mb
        })

    except subprocess.CalledProcessError as e:
        backup.status = 'failed'
        backup.mensaje_error = e.stderr
        backup.save()
        
        messages.error(request, f'❌ Error al crear el backup: {e.stderr}')
        return JsonResponse({'error': str(e.stderr)}, status=500)
    
    except Exception as e:
        backup.status = 'failed'
        backup.mensaje_error = str(e)
        backup.save()
        
        messages.error(request, f'❌ Error inesperado: {str(e)}')
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(es_superusuario)
def crear_backup_code(request):
    """Crea un backup del código fuente (Git push)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Crear registro de backup
    backup = Backup.objects.create(
        tipo='code',
        usuario=request.user,
        status='processing'
    )
    
    try:
        project_dir = settings.BASE_DIR
        
        # Git add
        subprocess.run(
            ['git', 'add', '-A'],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Git commit
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        commit_msg = f'Backup automático - {timestamp}'
        
        result = subprocess.run(
            ['git', 'commit', '-m', commit_msg],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        
        # Git push
        push_result = subprocess.run(
            ['git', 'push', 'origin', 'main'],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Obtener hash del commit
        hash_result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=True
        )
        commit_hash = hash_result.stdout.strip()
        
        # Actualizar registro
        backup.commit_hash = commit_hash
        backup.status = 'completed'
        backup.save()
        
        messages.success(
            request,
            f'✅ Backup de código fuente creado exitosamente (Commit: {commit_hash[:7]})'
        )
        
        return JsonResponse({
            'success': True,
            'backup_id': backup.id,
            'commit_hash': commit_hash
        })
        
    except subprocess.CalledProcessError as e:
        backup.status = 'failed'
        backup.mensaje_error = e.stderr
        backup.save()
        
        messages.error(request, f'❌ Error al crear el backup: {e.stderr}')
        return JsonResponse({'error': str(e.stderr)}, status=500)
    
    except Exception as e:
        backup.status = 'failed'
        backup.mensaje_error = str(e)
        backup.save()
        
        messages.error(request, f'❌ Error inesperado: {str(e)}')
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(es_superusuario)
def crear_backup_completo(request):
    """Crea un backup completo (DB + Code)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Crear registro de backup
    backup = Backup.objects.create(
        tipo='full',
        usuario=request.user,
        status='processing'
    )
    
    try:
        # Backup de DB
        db_response = crear_backup_db(request)
        if db_response.status_code != 200:
            raise Exception('Error al crear backup de base de datos')
        
        # Backup de código
        code_response = crear_backup_code(request)
        if code_response.status_code != 200:
            raise Exception('Error al crear backup de código')
        
        backup.status = 'completed'
        backup.save()
        
        messages.success(request, '✅ Backup completo creado exitosamente')
        
        return JsonResponse({
            'success': True,
            'backup_id': backup.id
        })
        
    except Exception as e:
        backup.status = 'failed'
        backup.mensaje_error = str(e)
        backup.save()
        
        messages.error(request, f'❌ Error al crear el backup completo: {str(e)}')
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(es_superusuario)
def descargar_backup(request, backup_id):
    """Descarga un archivo de backup"""
    try:
        backup = Backup.objects.get(id=backup_id)
        
        if not backup.archivo or not os.path.exists(backup.archivo):
            raise Http404('Archivo de backup no encontrado')
        
        return FileResponse(
            open(backup.archivo, 'rb'),
            as_attachment=True,
            filename=os.path.basename(backup.archivo)
        )
        
    except Backup.DoesNotExist:
        raise Http404('Backup no encontrado')


@login_required
@user_passes_test(es_superusuario)
def eliminar_backup(request, backup_id):
    """Elimina un backup"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        backup = Backup.objects.get(id=backup_id)
        
        # Eliminar archivo físico si existe
        if backup.archivo and os.path.exists(backup.archivo):
            os.remove(backup.archivo)
        
        # Eliminar registro
        backup.delete()
        
        messages.success(request, '✅ Backup eliminado exitosamente')
        return JsonResponse({'success': True})
        
    except Backup.DoesNotExist:
        return JsonResponse({'error': 'Backup no encontrado'}, status=404)
    except Exception as e:
        messages.error(request, f'❌ Error al eliminar el backup: {str(e)}')
        return JsonResponse({'error': str(e)}, status=500)