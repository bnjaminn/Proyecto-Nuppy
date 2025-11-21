"""
WSGI.PY - Configuración WSGI para el proyecto nuppy
====================================================
WSGI (Web Server Gateway Interface) es la interfaz estándar entre servidores web
y aplicaciones web Python. Este archivo expone la aplicación WSGI para que el
servidor web pueda comunicarse con Django.

Para más información sobre este archivo, ver:
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Establece el módulo de configuración antes de cargar la aplicación
# Indica a Django dónde encontrar el archivo settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nuppy.settings')

# Aplicación WSGI expuesta como variable a nivel de módulo
# Los servidores web (Apache, Nginx, gunicorn, etc.) usarán esta variable 'application'
# para comunicarse con la aplicación Django
application = get_wsgi_application()
