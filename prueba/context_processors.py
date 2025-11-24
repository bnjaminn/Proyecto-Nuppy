"""
CONTEXT PROCESSORS
==================
Context processors que agregan variables globales a todos los templates.
"""

def inactividad_detector(request):
    """
    Context processor que determina si se debe incluir el detector de inactividad.
    Solo se incluye en páginas que requieren autenticación (no en login).
    
    Returns:
        dict: Diccionario con 'include_inactividad_detector' como booleano
    """
    # No incluir el detector en la página de login o en la raíz
    ruta_actual = request.path
    es_login = '/login/' in ruta_actual or ruta_actual == '/' or ruta_actual == '/prueba/'
    
    # Incluir el detector si el usuario está autenticado o si no es la página de login
    # (esto asegura que funcione incluso si alguien accede a páginas protegidas sin login)
    usuario_autenticado = 'user_id' in request.session
    
    return {
        'include_inactividad_detector': not es_login
    }

