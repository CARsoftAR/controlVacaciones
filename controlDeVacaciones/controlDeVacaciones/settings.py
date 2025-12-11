# controlDeVacaciones/settings.py

import os
from pathlib import Path
from django.core.management.utils import get_random_secret_key

# Define el directorio base del proyecto
# 🛑 CORRECCIÓN CLAVE: Subimos TRES niveles para llegar al directorio raíz que contiene 'templates'
# Si settings.py está en el nivel 3, .parent.parent.parent lleva al nivel 0 (la raíz).
BASE_DIR = Path(__file__).resolve().parent
# ==============================================================================
# ⚠️ ADVERTENCIA: SEGURIDAD
# ==============================================================================
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', get_random_secret_key())
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = ['https://*.railway.app']

# ==============================================================================
# APLICACIONES (APPS)
# ==============================================================================

INSTALLED_APPS = [
    # Core de Django (debe ir primero)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Aplicaciones del proyecto
    'gestion', 
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', 
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', 
    'django.contrib.messages.middleware.MessageMiddleware', 
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Ajusta el nombre de tu proyecto principal según tu estructura real
ROOT_URLCONF = 'controlDeVacaciones.urls' 
WSGI_APPLICATION = 'controlDeVacaciones.wsgi.application'

# ==============================================================================
# PLANTILLAS (TEMPLATES) - Usando os.path.join para máxima compatibilidad
# ==============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # DIRS apunta al directorio 'templates' dentro del nivel de tu proyecto.
        'DIRS': [os.path.join(BASE_DIR, 'templates')], 
        'APP_DIRS': True, 
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ==============================================================================
# BASE DE DATOS (MySQL)
# ==============================================================================

import dj_database_url

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'vacacionesAbbamat'),
        'USER': os.getenv('DB_USER', 'root'),     
        'PASSWORD': os.getenv('DB_PASSWORD', '12345'),    
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),             
        'PORT': os.getenv('DB_PORT', '3306'),                 
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}

# Configuración automática para Railway/Render usando DATABASE_URL
if 'DATABASE_URL' in os.environ:
    DATABASES['default'] = dj_database_url.config(
        conn_max_age=600,
        ssl_require=True
    )


# ==============================================================================
# AUTENTICACIÓN Y CONTRASEÑAS
# ==============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# Importaciones existentes...
# ...

# Configuración de URL:
# 1. LOGIN_URL: La URL donde se encuentra el formulario de inicio de sesión.
#    Django por defecto busca 'accounts/login/'. Si usas tu propia vista, ajusta esta línea.
#    Si estás usando django.contrib.auth, déjala como '/accounts/login/' o usa el nombre de tu vista de login.
LOGIN_URL = '/login/'

# 🛑 Usamos la URL absoluta de tu dashboard para máxima robustez.
# Asumo que tu dashboard está mapeado a la URL /gestion/
LOGIN_REDIRECT_URL = '/gestion/' 

LOGOUT_REDIRECT_URL = '/login/' 

#    Si quieres que te redirija a un dashboard específico (ej. /gestion/dashboard/):
#    LOGIN_REDIRECT_URL = '/gestion/dashboard/' # <-- Usa esta si tienes una URL específica para el dashboard

# 3. LOGOUT_REDIRECT_URL (Opcional, pero recomendado):
#    A dónde enviar al usuario después de cerrar sesión.
#    Generalmente se envía de vuelta a la página de login o a la página principal.
LOGOUT_REDIRECT_URL = '/accounts/login/'



# ==============================================================================
# INTERNACIONALIZACIÓN Y LOCALIZACIÓN
# ==============================================================================

LANGUAGE_CODE = 'es-ar' 
TIME_ZONE = 'America/Argentina/Buenos_Aires' 
USE_I18N = True 
USE_TZ = True 


# ==============================================================================
# ARCHIVOS ESTÁTICOS (STATIC FILES)
# ==============================================================================

STATIC_URL = 'static/'

# Django buscará archivos estáticos adicionales en esta carpeta de proyecto
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# STATIC_ROOT: (Solo para Producción)
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage" 

# Configuración de archivos media (Si usaras subida de archivos/fotos)
# MEDIA_URL = '/media/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Tipo de campo para claves primarias (PK)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'