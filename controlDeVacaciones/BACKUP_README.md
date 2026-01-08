# 🛡️ Sistema de Backup y Restauración

## Descripción

Sistema completo de backup y restauración integrado en la aplicación de Control de Vacaciones ABBAMAT. Permite crear backups automáticos de la base de datos MySQL y del código fuente en GitHub.

## Características

### ✅ Funcionalidades Implementadas

1. **Backup de Base de Datos (MySQL)**
   - Exportación completa usando `mysqldump`
   - Incluye rutinas, triggers y eventos
   - Almacenamiento local en `backups/db/`
   - Registro del tamaño y fecha de creación

2. **Backup de Código Fuente (Git)**
   - Commit automático con timestamp
   - Push a GitHub (repositorio `controlVacaciones`)
   - Registro del hash del commit
   - Historial completo en GitHub

3. **Backup Completo**
   - Combina backup de DB + código
   - Ejecución secuencial automática

4. **Gestión de Backups**
   - Interfaz web premium con diseño moderno
   - Historial de backups realizados
   - Descarga de archivos de backup
   - Eliminación de backups antiguos
   - Estados: Pendiente, Procesando, Completado, Fallido

## Uso

### Acceso al Sistema

1. Inicia sesión como **Manager** o **Superusuario**
2. Ve a **Administración → Backups** en el menú principal
3. Selecciona el tipo de backup que deseas crear

### Tipos de Backup

#### 💾 Backup de Base de Datos
```bash
# Comando manual (opcional)
python manage.py backup_db
```

Crea un archivo `.sql` en `backups/db/` con la estructura completa de la base de datos.

#### 📦 Backup de Código Fuente
```bash
# Comando manual (opcional)
git add -A
git commit -m "Backup automático - YYYY-MM-DD HH:MM"
git push origin main
```

Sube todos los cambios del código a GitHub.

#### 🔄 Backup Completo
Ejecuta ambos backups en secuencia.

### Restauración de Base de Datos

```bash
# Comando manual
python manage.py restore_db backups/db/backup_vacacionesAbbamat_20260108_084400.sql
```

**⚠️ ADVERTENCIA:** La restauración sobrescribirá completamente la base de datos actual.

## Estructura de Archivos

```
controlDeVacaciones/
├── backups/                          # Directorio de backups (ignorado en Git)
│   └── db/
│       └── backup_*.sql
├── gestion/
│   ├── management/
│   │   └── commands/
│   │       ├── backup_db.py         # Comando para backup de DB
│   │       └── restore_db.py        # Comando para restaurar DB
│   ├── templates/
│   │   └── gestion/
│   │       └── backup_dashboard.html # Interfaz web
│   ├── backup_views.py              # Vistas del sistema de backup
│   ├── models.py                    # Modelo Backup agregado
│   └── urls.py                      # URLs del sistema de backup
└── .gitignore                       # Excluye backups/ y *.sql
```

## Modelo de Datos

### Backup
```python
class Backup(models.Model):
    tipo = CharField(choices=['db', 'code', 'full'])
    fecha_creacion = DateTimeField(auto_now_add=True)
    usuario = ForeignKey(User)
    archivo = CharField(max_length=500)
    tamaño = BigIntegerField()  # En bytes
    status = CharField(choices=['pending', 'processing', 'completed', 'failed'])
    mensaje_error = TextField()
    commit_hash = CharField(max_length=100)  # Para backups de código
```

## Seguridad

- ✅ Solo usuarios **superusuarios** pueden acceder al sistema de backup
- ✅ Los archivos de backup **NO se suben a GitHub** (`.gitignore`)
- ✅ Las contraseñas de DB se toman de `settings.py` (variables de entorno)
- ✅ Confirmación requerida para restauraciones

## Requisitos

### Software Necesario

- **MySQL Client Tools** (para `mysqldump` y `mysql`)
  ```bash
  # Windows
  # Incluido con MySQL Server o MySQL Workbench
  
  # Linux
  sudo apt-get install mysql-client
  ```

- **Git** (para backups de código)
  ```bash
  # Verificar instalación
  git --version
  ```

### Configuración de Git

Asegúrate de que Git esté configurado con credenciales válidas:

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"
```

## Automatización (Opcional)

### Backup Programado con Cron (Linux)

```bash
# Editar crontab
crontab -e

# Backup diario a las 2 AM
0 2 * * * cd /ruta/al/proyecto && python manage.py backup_db

# Backup semanal completo (Domingos a las 3 AM)
0 3 * * 0 cd /ruta/al/proyecto && python manage.py backup_db && git add -A && git commit -m "Backup semanal" && git push
```

### Backup Programado con Task Scheduler (Windows)

1. Abre **Programador de tareas**
2. Crea una nueva tarea básica
3. Configura el trigger (ej: diario a las 2 AM)
4. Acción: Ejecutar programa
   - Programa: `python`
   - Argumentos: `manage.py backup_db`
   - Directorio: `C:\Sistemas ABBAMAT\ControlDeVacaciones\controlDeVacaciones`

## Troubleshooting

### Error: "mysqldump: command not found"

**Solución:** Agrega MySQL a la variable PATH del sistema.

```bash
# Windows
set PATH=%PATH%;C:\Program Files\MySQL\MySQL Server 8.0\bin

# Linux
export PATH=$PATH:/usr/bin
```

### Error: "Permission denied" al hacer push

**Solución:** Configura las credenciales de Git o usa SSH.

```bash
# Configurar credenciales
git config credential.helper store
git push  # Te pedirá usuario y contraseña una vez
```

### Error: "Database access denied"

**Solución:** Verifica las credenciales en `settings.py` o variables de entorno.

## Mejoras Futuras

- [ ] Backups automáticos programados desde la interfaz web
- [ ] Compresión de archivos de backup (.sql.gz)
- [ ] Almacenamiento en la nube (AWS S3, Google Cloud Storage)
- [ ] Restauración desde la interfaz web
- [ ] Notificaciones por email al completar backups
- [ ] Retención automática (eliminar backups antiguos)
- [ ] Encriptación de backups sensibles

## Soporte

Para problemas o consultas, contacta al equipo de desarrollo de ABBAMAT.

---

**Última actualización:** 2026-01-08  
**Versión:** 1.0.0
