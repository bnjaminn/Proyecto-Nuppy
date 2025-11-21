"""
SETTINGS.PY - Configuraciones del proyecto Django "nuppy"
=========================================================
Este archivo contiene todas las configuraciones del proyecto Django.
Define aplicaciones instaladas, bases de datos, middleware, rutas estáticas, etc.

Generado por 'django-admin startproject' usando Django 5.2.7.

Para más información sobre este archivo, ver:
https://docs.djangoproject.com/en/5.2/topics/settings/

Para la lista completa de configuraciones y sus valores, ver:
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path

# CONFIGURACIÓN DE RUTAS DEL PROYECTO
# ====================================
# BASE_DIR: Ruta absoluta del directorio raíz del proyecto
# Se usa para construir rutas relativas a archivos del proyecto
# Path(__file__) obtiene la ruta de este archivo (settings.py)
# .resolve() convierte a ruta absoluta
# .parent.parent sube dos niveles: nuppy/nuppy/ -> nuppy/
BASE_DIR = Path(__file__).resolve().parent.parent


# CONFIGURACIONES DE SEGURIDAD Y DESARROLLO
# ==========================================
# ADVERTENCIA: Estas configuraciones son para desarrollo, no para producción
# Ver: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECRET_KEY: Clave secreta usada para firmar cookies, sesiones, etc.
# ADVERTENCIA: Mantener esta clave secreta en producción - NO exponer en repositorios públicos
SECRET_KEY = 'django-insecure-=nr5&1-d7yx@w(64-j4@b))2*m7zw+qosd76g4s860$w=-4)uw'

# DEBUG: Modo de depuración - muestra errores detallados en desarrollo
# ADVERTENCIA: NO ejecutar con DEBUG=True en producción por razones de seguridad
DEBUG = True

# ALLOWED_HOSTS: Lista de nombres de dominio/host permitidos para servir el sitio
# Vacío en desarrollo permite cualquier host. En producción debe contener dominios específicos
ALLOWED_HOSTS = []


# DEFINICIÓN DE APLICACIONES
# ===========================
# INSTALLED_APPS: Lista de aplicaciones Django instaladas en este proyecto
INSTALLED_APPS = [
    # Aplicaciones contribuidas por Django (incluidas por defecto)
    'django.contrib.admin',        # Panel de administración de Django
    'django.contrib.auth',         # Sistema de autenticación de usuarios
    'django.contrib.contenttypes', # Framework de tipos de contenido
    'django.contrib.sessions',     # Framework de sesiones
    'django.contrib.messages',     # Framework de mensajes flash
    'django.contrib.staticfiles',  # Framework para archivos estáticos (CSS, JS, imágenes)
    
    # Aplicación personalizada del proyecto
    'prueba',                      # Nuestra aplicación principal "prueba"
]

# MIDDLEWARE: Componentes que procesan requests y responses
# Se ejecutan en el orden especificado: de arriba hacia abajo en requests, inverso en responses
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',              # Mejoras de seguridad
    'django.contrib.sessions.middleware.SessionMiddleware',      # Manejo de sesiones
    'django.middleware.common.CommonMiddleware',                 # Funcionalidades comunes (ETags, etc.)
    'django.middleware.csrf.CsrfViewMiddleware',                 # Protección CSRF
    'django.contrib.auth.middleware.AuthenticationMiddleware',   # Autenticación de usuarios
    'django.contrib.messages.middleware.MessageMiddleware',      # Manejo de mensajes
    'django.middleware.clickjacking.XFrameOptionsMiddleware',    # Protección contra clickjacking
]

# ROOT_URLCONF: Módulo Python que contiene las URLs raíz del proyecto
ROOT_URLCONF = 'nuppy.urls'

# CONFIGURACIÓN DE TEMPLATES (PLANTILLAS HTML)
# =============================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',  # Motor de templates de Django
        'DIRS': [],                                                    # Directorios adicionales para buscar templates
        'APP_DIRS': True,                                              # Buscar templates en subdirectorios 'templates' de cada app
        'OPTIONS': {
            'context_processors': [
                # Procesadores de contexto - variables disponibles en todos los templates
                'django.template.context_processors.request',              # Objeto 'request' disponible
                'django.contrib.auth.context_processors.auth',             # Variables de usuario autenticado
                'django.contrib.messages.context_processors.messages',     # Mensajes flash
            ],
        },
    },
]

# WSGI_APPLICATION: Aplicación WSGI usada para servir el proyecto
WSGI_APPLICATION = 'nuppy.wsgi.application'


# CONFIGURACIÓN DE BASE DE DATOS SQLITE (PARA DJANGO ORM)
# ========================================================
# Django puede usar SQLite para el ORM mientras MongoDB se usa para otros datos
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Motor de base de datos SQLite
        'NAME': BASE_DIR / 'db.sqlite3',         # Ruta al archivo de base de datos SQLite
    }
}

# CONFIGURACIÓN DE BASE DE DATOS MONGODB CON MONGOENGINE
# ========================================================
# Importamos mongoengine para usar MongoDB como base de datos NoSQL
# MongoDB se usa para almacenar datos de documentos (como usuarios, logs, etc.)
import mongoengine

# Conectamos a MongoDB usando mongoengine
# db: nombre de la base de datos en MongoDB
# host: dirección del servidor MongoDB (localhost en el puerto 27017 por defecto)
mongoengine.connect(
    db="nuppy",
    host="mongodb://localhost:27017"
)


# VALIDACIÓN DE CONTRASEÑAS
# ==========================
# Configuraciones para validar la fortaleza de las contraseñas de usuarios
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        # Valida que la contraseña no sea similar a información del usuario (nombre, email, etc.)
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        # Valida que la contraseña tenga una longitud mínima
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        # Valida que la contraseña no esté en una lista de contraseñas comunes
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        # Valida que la contraseña no sea completamente numérica
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# INTERNACIONALIZACIÓN
# ====================
# Configuraciones de idioma, zona horaria y formatos de fecha/hora
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGE_CODE = 'en-us'      # Código de idioma por defecto (inglés de Estados Unidos)
TIME_ZONE = 'UTC'            # Zona horaria por defecto (UTC - Tiempo Universal Coordinado)
USE_I18N = True              # Habilita el sistema de internacionalización (traducción)
USE_TZ = True                # Usa zona horaria aware para fechas/horas (recomendado)


# ARCHIVOS ESTÁTICOS (CSS, JavaScript, Imágenes)
# ===============================================
# Configuración para servir archivos estáticos en desarrollo
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_URL = 'static/'       # URL base para archivos estáticos (ej: /static/css/style.css)

# ARCHIVOS MEDIA (Archivos subidos por usuarios)
# ===============================================
# Configuración para archivos subidos por usuarios (fotos de perfil, documentos, etc.)
MEDIA_URL = '/media/'                                    # URL base para archivos media (ej: /media/fotos_perfil/user.jpg)
MEDIA_ROOT = BASE_DIR / 'media'                         # Directorio físico donde se almacenan los archivos media

# CONFIGURACIÓN DE CLAVE PRIMARIA POR DEFECTO
# ============================================
# Tipo de campo usado automáticamente para claves primarias en modelos
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'   # Usa AutoField de 64 bits (BigAutoField)
