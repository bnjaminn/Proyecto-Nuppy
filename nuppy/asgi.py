"""
ASGI.PY - Configuración ASGI para el proyecto nuppy
====================================================
ASGI (Asynchronous Server Gateway Interface) es la interfaz estándar para aplicaciones
web asíncronas en Python. Permite usar características asíncronas como WebSockets.

Este archivo expone la aplicación ASGI como una variable a nivel de módulo llamada
``application``. Los servidores ASGI (Daphne, Uvicorn, etc.) usarán esta aplicación.

Para más información sobre este archivo, ver:
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Establece el módulo de configuración antes de cargar la aplicación
# Indica a Django dónde encontrar el archivo settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nuppy.settings')

# Aplicación ASGI expuesta como variable a nivel de módulo
# Los servidores ASGI usarán esta variable 'application' para comunicarse con Django
# Útil para aplicaciones que requieren funcionalidades asíncronas o WebSockets
application = get_asgi_application()
