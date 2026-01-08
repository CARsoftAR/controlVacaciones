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

        # Buscar mysqldump en ubicaciones comunes (Windows)
        mysqldump_paths = [
            'mysqldump',  # Si está en PATH
            r'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe',
            r'C:\Program Files\MySQL\MySQL Server 5.7\bin\mysqldump.exe',
            r'C:\xampp\mysql\bin\mysqldump.exe',
            r'C:\wamp64\bin\mysql\mysql8.0.27\bin\mysqldump.exe',
        ]
        
        mysqldump_cmd = None
        for path in mysqldump_paths:
            try:
                # Verificar si el comando existe
                test_result = subprocess.run(
                    [path, '--version'],
                    capture_output=True,
                    timeout=5
                )
                if test_result.returncode == 0:
                    mysqldump_cmd = path
                    break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        if not mysqldump_cmd:
            raise Exception(
                'No se encontró mysqldump. Instala MySQL Client Tools o agrega MySQL al PATH del sistema.'
            )

        # Comando mysqldump
        dump_cmd = [
            mysqldump_cmd,
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
                check=True,
                timeout=300  # 5 minutos máximo
            )

        # Obtener tamaño del archivo
        file_size = os.path.getsize(backup_file)

        # Actualizar registro
        backup.archivo = backup_file
        backup.tamaño = file_size
        backup.status = 'completed'
        backup.save()

        return JsonResponse({
            'success': True,
            'backup_id': backup.id,
            'archivo': os.path.basename(backup_file),
            'tamaño_mb': backup.tamaño_mb,
            'message': f'Backup creado exitosamente ({backup.tamaño_mb} MB)'
        })

    except subprocess.CalledProcessError as e:
        backup.status = 'failed'
        error_msg = e.stderr if e.stderr else str(e)
        backup.mensaje_error = error_msg
        backup.save()
        
        return JsonResponse({
            'success': False,
            'error': f'Error de mysqldump: {error_msg}'
        }, status=500)
    
    except subprocess.TimeoutExpired:
        backup.status = 'failed'
        backup.mensaje_error = 'Timeout: El backup tardó más de 5 minutos'
        backup.save()
        
        return JsonResponse({
            'success': False,
            'error': 'El backup tardó demasiado tiempo. Intenta con una base de datos más pequeña.'
        }, status=500)
    
    except Exception as e:
        backup.status = 'failed'
        backup.mensaje_error = str(e)
        backup.save()
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


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
        
        return JsonResponse({
            'success': True,
            'backup_id': backup.id,
            'commit_hash': commit_hash,
            'message': f'Backup de código creado exitosamente (Commit: {commit_hash[:7]})'
        })
        
    except subprocess.CalledProcessError as e:
        backup.status = 'failed'
        error_msg = e.stderr if e.stderr else str(e)
        backup.mensaje_error = error_msg
        backup.save()
        
        return JsonResponse({
            'success': False,
            'error': f'Error de Git: {error_msg}'
        }, status=500)
    
    except Exception as e:
        backup.status = 'failed'
        backup.mensaje_error = str(e)
        backup.save()
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


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
        db_data = db_response.content.decode('utf-8')
        
        if db_response.status_code != 200:
            raise Exception('Error al crear backup de base de datos')
        
        # Backup de código
        code_response = crear_backup_code(request)
        if code_response.status_code != 200:
            raise Exception('Error al crear backup de código')
        
        backup.status = 'completed'
        backup.save()
        
        return JsonResponse({
            'success': True,
            'backup_id': backup.id,
            'message': 'Backup completo creado exitosamente'
        })
        
    except Exception as e:
        backup.status = 'failed'
        backup.mensaje_error = str(e)
        backup.save()
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


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
        
        return JsonResponse({
            'success': True,
            'message': 'Backup eliminado exitosamente'
        })
        
    except Backup.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Backup no encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)