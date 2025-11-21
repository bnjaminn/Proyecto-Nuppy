"""
URLS.PY - Configuración de URLs raíz del proyecto nuppy
========================================================
Este archivo define las rutas principales del proyecto Django.
Las URLs se mapean a vistas (views) que procesan las peticiones HTTP.

La lista `urlpatterns` enruta las URLs a las vistas. Para más información ver:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/

Ejemplos de uso:
- Vistas basadas en funciones: path('', views.home, name='home')
- Vistas basadas en clases: path('', Home.as_view(), name='home')
- Incluir otras configuraciones de URL: path('app/', include('app.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# PATRONES DE URL PRINCIPALES
# ============================
# Define las rutas del proyecto y las vistas que las manejan
urlpatterns = [
    # Ruta para el panel de administración de Django
    # Accesible en: http://localhost:8000/admin/
    path('admin/', admin.site.urls),
    
    # Incluye las URLs de la aplicación 'prueba'
    # Todas las URLs de 'prueba.urls' estarán bajo el prefijo 'prueba/'
    # Ejemplo: path('prueba/', ...) en prueba/urls.py será accesible en /prueba/...
    path('prueba/', include("prueba.urls")),
]

# CONFIGURACIÓN PARA SERVIR ARCHIVOS MEDIA EN DESARROLLO
# ========================================================
# Solo en modo DEBUG, Django sirve archivos media directamente
# En producción, estos archivos deben ser servidos por el servidor web (nginx, Apache, etc.)
if settings.DEBUG:
    # Añade una ruta para servir archivos media desde el directorio MEDIA_ROOT
    # Los archivos en /media/ serán servidos desde el directorio especificado en MEDIA_ROOT
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
