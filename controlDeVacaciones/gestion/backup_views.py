import os
import subprocess
import shutil
import tempfile
import zipfile
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse, FileResponse, Http404
from django.core.management import call_command
from io import StringIO
from pathlib import Path
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


def _ejecutar_backup_db(backup_id=None):
    """Lógica principal para crear backup de DB, puede usarse internamente"""
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

    # Buscar mysqldump
    mysqldump_paths = [
        'mysqldump',
        r'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe',
        r'C:\Program Files\MySQL\MySQL Server 5.7\bin\mysqldump.exe',
        r'C:\xampp\mysql\bin\mysqldump.exe',
        r'C:\wamp64\bin\mysql\mysql8.0.27\bin\mysqldump.exe',
    ]
    
    mysqldump_cmd = None
    for path in mysqldump_paths:
        try:
            test_result = subprocess.run([path, '--version'], capture_output=True, timeout=5)
            if test_result.returncode == 0:
                mysqldump_cmd = path
                break
        except: continue
    
    if not mysqldump_cmd:
        raise Exception('No se encontró mysqldump.')

    dump_cmd = [
        mysqldump_cmd, f'--host={db_host}', f'--port={db_port}',
        f'--user={db_user}', f'--password={db_password}',
        '--single-transaction', '--routines', '--triggers', '--events', db_name
    ]

    with open(backup_file, 'w', encoding='utf-8') as f:
        subprocess.run(dump_cmd, stdout=f, stderr=subprocess.PIPE, text=True, check=True, timeout=300)

    file_size = os.path.getsize(backup_file)
    return backup_file, file_size


@login_required
@user_passes_test(es_superusuario)
def crear_backup_db(request):
    """Crea un backup de la base de datos"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    backup = Backup.objects.create(tipo='db', usuario=request.user, status='processing')
    
    try:
        backup_file, file_size = _ejecutar_backup_db(backup.id)
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
    except Exception as e:
        backup.status = 'failed'
        backup.mensaje_error = str(e)
        backup.save()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def _ejecutar_backup_code():
    """Lógica principal para crear backup de código (ZIP + Git push)"""
    # Buscamos la raíz del proyecto subiendo niveles desde BASE_DIR
    project_dir = str(settings.BASE_DIR)
    
    # Subir hasta encontrar la carpeta que contiene .git (raíz del repo)
    # o hasta un máximo de 5 niveles para evitar bucles infinitos
    current = os.path.abspath(project_dir)
    found_root = current
    
    for _ in range(5):
        # Indicadores fuertes de raíz de proyecto
        is_root = (
            os.path.exists(os.path.join(current, '.git')) or 
            os.path.exists(os.path.join(current, 'requirements.txt')) or 
            os.path.exists(os.path.join(current, 'Dockerfile'))
        )
        
        if is_root:
            found_root = current
            break
            
        # Si tiene manage.py, es un candidato (backend django), pero seguimos buscando la raíz real
        if os.path.exists(os.path.join(current, 'manage.py')):
             found_root = current
             
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
        
    project_dir = found_root
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 1. Crear ZIP del proyecto
    output_dir = os.path.join(settings.BASE_DIR, 'backups', 'code')
    os.makedirs(output_dir, exist_ok=True)
    zip_file = os.path.join(output_dir, f'backup_code_{timestamp}.zip')
    
    # Lista de carpetas/archivos a ignorar
    ignore_list = ['backups', '.git', '__pycache__', 'venv', 'env', 'node_modules', 'ngrok.exe', '.gemini', '.agent']
    
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_dir):
            # Modificar dirs in-place para que os.walk ignore las carpetas de la ignore_list
            dirs[:] = [d for d in dirs if d not in ignore_list]
            
            for file in files:
                if file in ignore_list:
                    continue
                file_path = os.path.join(root, file)
                # No incluir el propio archivo zip que estamos creando si coincidiera
                if file_path == zip_file:
                    continue
                    
                arcname = os.path.relpath(file_path, project_dir)
                zipf.write(file_path, arcname)

    file_size = os.path.getsize(zip_file)

    # 2. Git push (Opcional, no falla si no hay git)
    commit_hash = ""
    try:
        subprocess.run(['git', 'add', '-A'], cwd=project_dir, check=True, capture_output=True)
        commit_msg = f'Backup automático - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
        subprocess.run(['git', 'commit', '-m', commit_msg], cwd=project_dir, capture_output=True)
        subprocess.run(['git', 'push', 'origin', 'main'], cwd=project_dir, capture_output=True)
        hash_res = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=project_dir, capture_output=True, text=True)
        commit_hash = hash_res.stdout.strip()
    except:
        pass

    return zip_file, file_size, commit_hash


@login_required
@user_passes_test(es_superusuario)
def crear_backup_code(request):
    """Crea un backup del código fuente"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    backup = Backup.objects.create(tipo='code', usuario=request.user, status='processing')
    
    try:
        zip_file, file_size, commit_hash = _ejecutar_backup_code()
        
        backup.archivo = zip_file
        backup.tamaño = file_size
        backup.commit_hash = commit_hash
        backup.status = 'completed'
        backup.save()
        
        msg = f'Backup de código creado exitosamente ({backup.tamaño_mb} MB)'
        if commit_hash: msg += f' (Commit: {commit_hash[:7]})'
        
        return JsonResponse({
            'success': True,
            'backup_id': backup.id,
            'archivo': os.path.basename(zip_file),
            'tamaño_mb': backup.tamaño_mb,
            'message': msg
        })
    except Exception as e:
        backup.status = 'failed'
        backup.mensaje_error = str(e)
        backup.save()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(es_superusuario)
def crear_backup_completo(request):
    """Crea un backup completo (ZIP de DB + Code)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    backup = Backup.objects.create(tipo='full', usuario=request.user, status='processing')
    
    try:
        # 1. Ejecutar Backup de DB
        db_file, _ = _ejecutar_backup_db()
        
        # 2. Ejecutar Backup de código
        code_zip, _, commit_hash = _ejecutar_backup_code()
        
        # 3. Crear el bundle final (Un ZIP que contiene ambos)
        output_dir = os.path.join(settings.BASE_DIR, 'backups', 'full')
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        full_zip_path = os.path.join(output_dir, f'backup_completo_{timestamp}.zip')
        
        with zipfile.ZipFile(full_zip_path, 'w') as zipf:
            zipf.write(db_file, os.path.basename(db_file))
            zipf.write(code_zip, os.path.basename(code_zip))
            
        backup.archivo = full_zip_path
        backup.tamaño = os.path.getsize(full_zip_path)
        backup.commit_hash = commit_hash
        backup.status = 'completed'
        backup.save()
        
        # Opcional: Limpiar los archivos individuales temporales si se desea, 
        # pero aquí los mantenemos en sus carpetas para que aparezcan en el historial
        
        return JsonResponse({
            'success': True,
            'backup_id': backup.id,
            'tamaño_mb': backup.tamaño_mb,
            'message': f'Backup completo creado exitosamente ({backup.tamaño_mb} MB)'
        })
        
    except Exception as e:
        backup.status = 'failed'
        backup.mensaje_error = str(e)
        backup.save()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


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