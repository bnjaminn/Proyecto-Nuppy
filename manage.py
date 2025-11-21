#!/usr/bin/env python
"""
MANAGE.PY - Utilidad de línea de comandos de Django para tareas administrativas
===============================================================================
Este archivo es el punto de entrada para ejecutar comandos administrativos de Django.
Permite ejecutar comandos como: python manage.py runserver, python manage.py migrate, etc.
"""
import os
import sys


def main():
    """
    Función principal que ejecuta comandos administrativos de Django.
    
    Flujo:
    1. Establece la variable de entorno DJANGO_SETTINGS_MODULE para indicar dónde están las configuraciones
    2. Importa execute_from_command_line de Django
    3. Ejecuta el comando pasado desde la línea de comandos
    """
    # Establece el módulo de configuración por defecto como 'nuppy.settings'
    # Esto le dice a Django dónde encontrar el archivo settings.py del proyecto
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nuppy.settings')
    
    try:
        # Intenta importar la función que ejecuta los comandos de Django
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Si Django no está instalado o no está disponible en el PYTHONPATH
        # Lanza un error informativo para ayudar al usuario a diagnosticar el problema
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Ejecuta el comando pasado desde la línea de comandos (sys.argv contiene los argumentos)
    # Ejemplo: python manage.py runserver -> sys.argv = ['manage.py', 'runserver']
    execute_from_command_line(sys.argv)


# Solo ejecuta main() si el script se ejecuta directamente (no si se importa)
if __name__ == '__main__':
    main()
