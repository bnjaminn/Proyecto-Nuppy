"""
==========================================================
Este archivo define las rutas (URLs) de la aplicación y las vistas que las manejan.
Cada ruta se mapea a una función vista que procesa la petición HTTP.

Todas las URLs están bajo el prefijo 'prueba/' (definido en nuppy/urls.py)
Ejemplo: path('home/', ...) es accesible en /prueba/home/
"""

from django.urls import path, include
# Importamos todas las vistas que manejarán las peticiones HTTP
from .views import listar_usuarios, login_view, home_view, logout_view, contacto_view, ingresar_view, ingresar_calificacion, administrar_view, crear_usuario_view, eliminar_usuarios_view, obtener_usuario_view, modificar_usuario_view, ver_logs_view, guardar_factores_view, calcular_factores_view, buscar_calificaciones_view, obtener_calificacion_view, eliminar_calificacion_view, obtener_logs_calificacion_view, copiar_calificacion_view, cargar_factor_view, cargar_monto_view, calcular_factores_masivo_view, preview_factor_view, preview_monto_view, exportar_calificaciones_view

# PATRONES DE URL
# ===============
# Define las rutas de la aplicación y las vistas que las manejan
# Formato: path('ruta/', vista_funcion, name='nombre_identificador')
urlpatterns = [
    # RUTAS DE NAVEGACIÓN PRINCIPAL
    # ===============================
    path("listar/", listar_usuarios, name="listar_usuarios"),  # Lista todos los usuarios
    path('home/', home_view, name='home'),                      # Página principal del dashboard
    path('login/', login_view, name='login'),                   # Página de inicio de sesión
    path('logout/', logout_view, name='logout'),                # Cerrar sesión
    path('contacto/', contacto_view, name='contacto'),         # Página de contacto de Nuam
    
    # RUTAS DE CALIFICACIONES (INGRESO Y GESTIÓN)
    # ============================================
    path('ingresar/', ingresar_view, name='ingresar'),                              # Ingresar calificación básica (modal 1)
    path('ingresar-calificacion/', ingresar_calificacion, name='ingresar_calificacion'),  # Ingresar calificación con montos
    path('buscar-calificaciones/', buscar_calificaciones_view, name='buscar_calificaciones'),  # Buscar calificaciones con filtros (AJAX)
    path('exportar-calificaciones/', exportar_calificaciones_view, name='exportar_calificaciones'),  # Exportar calificaciones a CSV
    path('obtener-calificacion/<str:calificacion_id>/', obtener_calificacion_view, name='obtener_calificacion'),  # Obtener una calificación específica
    path('eliminar-calificacion/<str:calificacion_id>/', eliminar_calificacion_view, name='eliminar_calificacion'),  # Eliminar una calificación
    path('copiar-calificacion/<str:calificacion_id>/', copiar_calificacion_view, name='copiar_calificacion'),  # Copiar una calificación completa
    
    # RUTAS DE FACTORES Y MONTOS (CÁLCULOS)
    # ======================================
    path('guardar-factores/', guardar_factores_view, name='guardar_factores'),           # Guardar factores calculados
    path('calcular-factores/', calcular_factores_view, name='calcular_factores'),         # Calcular factores desde montos
    path('calcular-factores-masivo/', calcular_factores_masivo_view, name='calcular_factores_masivo'),  # Calcular factores en carga masiva
    
    # RUTAS DE CARGA MASIVA (CSV)
    # ============================
    path('preview-factor/', preview_factor_view, name='preview_factor'),  # Previsualizar CSV con factores
    path('preview-monto/', preview_monto_view, name='preview_monto'),     # Previsualizar CSV con montos
    path('cargar-factor/', cargar_factor_view, name='cargar_factor'),     # Cargar CSV con factores ya calculados
    path('cargar-monto/', cargar_monto_view, name='cargar_monto'),        # Cargar CSV con montos (factores se calculan)
    
    # RUTAS DE ADMINISTRACIÓN DE USUARIOS
    # ====================================
    path('administrar/', administrar_view, name='administrar'),                        # Página de administración de usuarios
    path('crear_usuario/', crear_usuario_view, name='crear_usuario'),                  # Crear nuevo usuario (AJAX POST)
    path('eliminar_usuarios/', eliminar_usuarios_view, name='eliminar_usuarios'),      # Eliminar usuarios (AJAX POST)
    path('obtener-usuario/<str:user_id>/', obtener_usuario_view, name='obtener_usuario'),  # Obtener datos de un usuario (AJAX GET)
    path('modificar-usuario/', modificar_usuario_view, name='modificar_usuario'),      # Modificar usuario existente (AJAX POST)
    
    # RUTAS DE LOGS Y AUDITORÍA
    # ==========================
    path('ver-logs/', ver_logs_view, name='ver_logs'),                                # Ver todos los logs del sistema
    path('obtener-logs-calificacion/<str:calificacion_id>/', obtener_logs_calificacion_view, name='obtener_logs_calificacion'),  # Obtener logs de una calificación específica
]
