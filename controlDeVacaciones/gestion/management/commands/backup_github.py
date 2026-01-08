# gestion/management/commands/backup_github.py

import os
import subprocess
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Sincroniza el código fuente con GitHub'

    def handle(self, *args, **options):
        project_dir = str(settings.BASE_DIR)
        
        # Buscar raíz real
        current = os.path.abspath(project_dir)
        found_root = current
        for _ in range(5):
            if os.path.exists(os.path.join(current, '.git')):
                found_root = current
                break
            parent = os.path.dirname(current)
            if parent == current: break
            current = parent
        
        project_dir = found_root
        
        try:
            self.stdout.write(self.style.WARNING(f'Verificando cambios en {project_dir}...'))
            
            # Verificar cambios
            status_res = subprocess.run(['git', 'status', '--porcelain'], cwd=project_dir, capture_output=True, text=True)
            
            if status_res.stdout.strip():
                self.stdout.write(self.style.SUCCESS('Hay cambios para commitear.'))
                subprocess.run(['git', 'add', '-A'], cwd=project_dir, check=True)
                commit_msg = f'Backup automático (CLI) - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
                subprocess.run(['git', 'commit', '-m', commit_msg], cwd=project_dir, check=True)
                
                self.stdout.write(self.style.WARNING('Haciendo push a origin main...'))
                subprocess.run(['git', 'push', 'origin', 'main'], cwd=project_dir, check=True)
                self.stdout.write(self.style.SUCCESS('✅ Sincronización con GitHub completada exitosamente.'))
            else:
                self.stdout.write(self.style.SUCCESS('El código ya está al día localmente.'))
                self.stdout.write(self.style.WARNING('Intentando push por si hay commits pendientes...'))
                subprocess.run(['git', 'push', 'origin', 'main'], cwd=project_dir, check=True)
                self.stdout.write(self.style.SUCCESS('✅ Push completado (si había algo pendiente).'))

        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'❌ Error en Git: {str(e)}'))
            raise
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error inesperado: {str(e)}'))
            raise
