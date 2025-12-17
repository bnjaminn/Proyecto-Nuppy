def inactividad_detector(request):
    ruta_actual = request.path
    es_login = '/login/' in ruta_actual or ruta_actual == '/' or ruta_actual == '/prueba/'
    
    usuario_autenticado = 'user_id' in request.session
    
    return {
        'include_inactividad_detector': not es_login
    }

