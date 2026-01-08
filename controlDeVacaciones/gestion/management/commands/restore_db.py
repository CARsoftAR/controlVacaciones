# gestion/management/commands/restore_db.py

import os
import subprocess
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Restaura la base de datos MySQL desde un archivo de backup'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help='Ruta al archivo de backup (.sql) a restaurar'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar restauración sin confirmación'
        )

    def handle(self, *args, **options):
        backup_file = options['backup_file']
        
        # Verificar que el archivo existe
        if not os.path.exists(backup_file):
            raise CommandError(f'❌ El archivo {backup_file} no existe')

        # Configuración de la base de datos
        db_config = settings.DATABASES['default']
        db_name = db_config['NAME']
        db_user = db_config['USER']
        db_password = db_config['PASSWORD']
        db_host = db_config['HOST']
        db_port = db_config['PORT']

        # Confirmación si no se usa --force
        if not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  ADVERTENCIA: Esta operación sobrescribirá la base de datos "{db_name}".\n'
                    f'   Archivo de backup: {backup_file}\n'
                )
            )
            confirm = input('¿Desea continuar? (escriba "SI" para confirmar): ')
            if confirm != 'SI':
                self.stdout.write(self.style.ERROR('Operación cancelada'))
                return

        # Comando mysql para restaurar
        restore_cmd = [
            'mysql',
            f'--host={db_host}',
            f'--port={db_port}',
            f'--user={db_user}',
            f'--password={db_password}',
            db_name
        ]

        try:
            self.stdout.write(
                self.style.WARNING(f'Restaurando base de datos {db_name}...')
            )
            
            with open(backup_file, 'r', encoding='utf-8') as f:
                result = subprocess.run(
                    restore_cmd,
                    stdin=f,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Base de datos restaurada exitosamente desde:\n'
                    f'   {backup_file}'
                )
            )

        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Error al restaurar la base de datos:\n{e.stderr}'
                )
            )
            raise
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error inesperado: {str(e)}')
            )
            raise
