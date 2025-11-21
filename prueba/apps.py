"""
==================================================
Este archivo define la configuración de la aplicación Django 'prueba'.
Se usa para configurar el comportamiento de la aplicación dentro del proyecto.
"""

from django.apps import AppConfig


# CONFIGURACIÓN DE LA APLICACIÓN
# ===============================
# Clase que define la configuración de la aplicación 'prueba'
class PruebaConfig(AppConfig):
    # Tipo de campo automático para claves primarias en modelos Django ORM
    # No se usa en este proyecto porque usamos MongoDB (MongoEngine)
    default_auto_field = 'django.db.models.BigAutoField'
    
    # Nombre de la aplicación (debe coincidir con el nombre del directorio)
    name = 'prueba'
