# gestion/management/commands/backup_db.py

import os
import subprocess
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Crea un backup de la base de datos MySQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='backups/db',
            help='Directorio donde guardar el backup'
        )

    def handle(self, *args, **options):
        # Configuración de la base de datos
        db_config = settings.DATABASES['default']
        db_name = db_config['NAME']
        db_user = db_config['USER']
        db_password = db_config['PASSWORD']
        db_host = db_config['HOST']
        db_port = db_config['PORT']

        # Crear directorio de backups si no existe
        output_dir = os.path.join(settings.BASE_DIR, options['output_dir'])
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

        try:
            self.stdout.write(self.style.WARNING(f'Creando backup de la base de datos {db_name}...'))
            
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
            size_mb = file_size / (1024 * 1024)

            self.stdout.write(
                self.style.SUCCESS(
                    f'OK - Backup creado exitosamente:\n'
                    f'   Archivo: {backup_file}\n'
                    f'   Tamaño: {size_mb:.2f} MB'
                )
            )
            
            return backup_file

        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(
                    f'ERROR al crear el backup:\n{e.stderr}'
                )
            )
            # Eliminar archivo parcial si existe
            if os.path.exists(backup_file):
                os.remove(backup_file)
            raise
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'ERROR inesperado: {str(e)}')
            )
            raise
