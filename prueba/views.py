"""
===========================================================
Este archivo contiene todas las vistas que procesan las peticiones.
Las vistas manejan la lógica de negocio, interactúan con la base de datos
y devuelven respuestas HTML o JSON.

Estructura:
- Funciones auxiliares: Funciones de utilidad compartidas
- Vistas de autenticación: Login, logout
- Vistas de navegación: Home, administración
- Vistas de usuarios: Crear, modificar, eliminar usuarios
- Vistas de calificaciones: Crear, modificar, eliminar, buscar calificaciones
- Vistas de factores/montos: Calcular factores, guardar montos
- Vistas de carga masiva: Cargar CSV, previsualizar archivos
- Vistas de logs: Ver registros de auditoría
"""

# IMPORTACIONES
# ======================================
import json      # Para manejar datos JSON en las respuestas de API
import bcrypt    # Para hashear contraseñas de forma segura
import re        # Para expresiones regulares - usado en _extraer_object_id() para parsear DBRef
import os        # Para operaciones del sistema de archivos (rutas, extensiones)
import datetime  # Para manejar fechas y horas
from django.shortcuts import render, redirect  # render: renderizar templates HTML | redirect: redirigir a otras URLs
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseServerError  # Respuestas HTTP: Forbidden(403), JSON, ServerError(500)
from django.views.decorators.http import require_POST, require_GET  # Decoradores para restringir métodos HTTP (POST/GET)
from django.contrib import messages  # Para mensajes flash al usuario
from django.conf import settings  # Acceso a configuración de Django (MEDIA_ROOT, etc.)
from mongoengine.errors import DoesNotExist  # Excepción cuando un documento no existe en MongoDB
from bson import ObjectId  # Tipo ObjectId de MongoDB - usado para IDs y operaciones con documentos
try:
    from PIL import Image  # Librería para procesamiento de imágenes (redimensionar fotos)
    HAS_PIL = True
except ImportError:
    HAS_PIL = False  # Si no está instalado Pillow, las imágenes no se redimensionarán pero la app funcionará
from .formulario import LoginForm, CalificacionModalForm, UsuarioForm, UsuarioUpdateForm, FactoresForm, MontosForm  # Formularios Django para validación
from .models import usuarios, Calificacion, Log  # Modelos de MongoDB (Documentos) para interactuar con la base de datos


# =====================================================================
# FUNCIONES AUXILIARES (funciones que realizan tareas pequeñas y reutilizables)
# =====================================================================

# FUNCIÓN AUXILIAR: EXTRAER OBJECTID
# ===================================
# Extrae el ObjectId desde un DBRef, ObjectId o cualquier otro tipo.
# Se usa para obtener el ID de documentos referenciados en MongoDB.
# Retorna el string del ObjectId o None si no puede extraerlo.
def _extraer_object_id(valor):
    """
    Extrae el ObjectId desde un DBRef, ObjectId o cualquier otro tipo.
    Retorna el string del ObjectId o None si no puede extraerlo.
    
    Argumentos:
        valor: Puede ser un DBRef, ObjectId, string, o cualquier objeto que contenga un ID
        
    Returns (lo que devuelve la funcion):
        str: String del ObjectId si se puede extraer, None en caso contrario
    """
    if not valor:
        return None
    
    try:
        # Si es un DBRef (cuando usas no_dereference())
        # MongoEngine DBRef tiene el ObjectId en el atributo 'id'
        if hasattr(valor, 'id'):
            obj_id = valor.id
            # Si el atributo id es un ObjectId, convertirlo a string
            if isinstance(obj_id, ObjectId):
                return str(obj_id)
            # Si ya es string, validar que sea un ObjectId válido
            elif isinstance(obj_id, str):
                ObjectId(obj_id)  # Validar formato
                return obj_id
            else:
                return str(obj_id)
        # Si ya es un ObjectId directamente
        elif isinstance(valor, ObjectId):
            return str(valor)
        # Si es una string que representa un ObjectId
        elif isinstance(valor, str):
            # Si contiene DBRef, extraer el ObjectId del string
            if "DBRef" in valor and "ObjectId" in valor:
                # Extraer ObjectId de strings como "DBRef('usuarios', ObjectId('690540200087edb1055cda79'))"
                match = re.search(r"ObjectId\('([a-f0-9]{24})'\)", valor)
                if match:
                    return match.group(1)
            # Intentar convertir a ObjectId para validar y luego retornar string
            ObjectId(valor)
            return valor
        # Si tiene atributo pk (algunos objetos MongoEngine)
        elif hasattr(valor, 'pk'):
            return str(valor.pk)
        # Último recurso: convertir a string y verificar si es ObjectId válido
        else:
            str_valor = str(valor)
            # Si el string contiene un DBRef, intentar extraerlo
            if "DBRef" in str_valor and "ObjectId" in str_valor:
                match = re.search(r"ObjectId\('([a-f0-9]{24})'\)", str_valor)
                if match:
                    return match.group(1)
            return str_valor
    except Exception as e:
        print(f"Error al extraer ObjectId: {e}, valor: {valor}")
        return None




# FUNCIÓN AUXILIAR: GUARDAR FOTO DE PERFIL
# =========================================
# Guarda la foto de perfil del usuario y retorna la ruta.
# Valida el tamaño y formato del archivo, redimensiona la imagen si es muy grande.
def _guardar_foto_perfil(archivo, usuario_id):
    """
    Guarda la foto de perfil del usuario y retorna la ruta.
    Redimensiona la imagen si es muy grande (máximo 500x500px).
    
    Argumentos:
        archivo: Archivo de imagen subido por el usuario
        usuario_id: ID del usuario para crear un nombre único
        
    Returns (lo que devuelve la funcion):
        str: Ruta relativa de la foto guardada (ej: 'fotos_perfil/usuario_123_foto.jpg')
        
    Raises (excepciones que puede lanzar la funcion):
        ValueError: Si el archivo es muy grande o tiene formato inválido
    """
    if not archivo:
        return None
    
    # Validar tamaño (5MB máximo)
    if archivo.size > 5 * 1024 * 1024:
        raise ValueError("La imagen es demasiado grande. Máximo 5MB.")
    
    # Validar tipo de archivo
    extension = os.path.splitext(archivo.name)[1].lower()
    if extension not in ['.jpg', '.jpeg', '.png', '.gif']:
        raise ValueError("Formato de imagen no válido. Use JPG, PNG o GIF.")
    
    # Crear directorio si no existe
    media_dir = settings.MEDIA_ROOT / 'fotos_perfil'
    media_dir.mkdir(parents=True, exist_ok=True)
    
    # Nombre único del archivo
    nombre_archivo = f"usuario_{usuario_id}_{archivo.name}"
    ruta_completa = media_dir / nombre_archivo
    
    # Guardar archivo
    with open(ruta_completa, 'wb+') as destino:
        for chunk in archivo.chunks():
            destino.write(chunk)
    
    # Redimensionar si es necesario (máximo 500x500)
    if HAS_PIL:
        try:
            img = Image.open(ruta_completa)
            if img.width > 500 or img.height > 500:
                img.thumbnail((500, 500), Image.Resampling.LANCZOS)
                img.save(ruta_completa, optimize=True, quality=85)
        except Exception as e:
            print(f"Error al redimensionar imagen: {e}")
    else:
        print("Pillow no está instalado. Las imágenes no se redimensionarán automáticamente.")
    
    # Retornar ruta relativa para guardar en MongoDB
    return f"fotos_perfil/{nombre_archivo}"



# FUNCIONES AUXILIARES: HASH DE CONTRASEÑAS
# ==========================================
# Funciones para hashear y verificar contraseñas usando bcrypt
# Bcrypt es un algoritmo de hashing seguro y ampliamente usado

def _hash_password(password):
    """
    Hashea una contraseña usando bcrypt.
    
    Argumentos:
        password: Contraseña en texto plano
        
    Returns (lo que devuelve la funcion):
        str: Contraseña hasheada en formato bcrypt
    """
    if not password:
        return None
    # Generar salt y hashear la contraseña
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def _check_password(password, hashed_password):
    """
    Verifica si una contraseña coincide con su hash usando bcrypt.
    
    Argumentos:
        password: Contraseña en texto plano a verificar
        hashed_password: Contraseña hasheada almacenada en la base de datos
        
    Returns (lo que devuelve la funcion):
        bool: True si la contraseña coincide, False en caso contrario
    """
    if not password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False





# FUNCIÓN AUXILIAR: CREAR LOG 
# ============================
# Guarda un registro de log con información sobre la acción realizada.
# Se usa para auditoría de todas las operaciones del sistema.
def _crear_log(usuario_obj, accion_str, documento_afectado=None, usuario_afectado=None, cambios_detallados=None, hash_archivo_csv=None):
    """
    Guarda un registro de log con información sobre la acción realizada.
    
    Argumentos:
        usuario_obj: Objeto usuario que realizó la acción
        accion_str: String con la acción realizada (debe estar en Log.ACCION_CHOICES)
        documento_afectado: Calificación afectada por la acción (opcional)
        usuario_afectado: Usuario afectado por la acción (opcional)
        cambios_detallados: Lista de diccionarios con los cambios realizados (opcional)
                            Formato: [{"campo": "nombre", "valor_anterior": "val1", "valor_nuevo": "val2"}]
        hash_archivo_csv: Hash SHA-256 del archivo CSV para cargas masivas (opcional)
    """
    try:
        cambios_json = None
        if cambios_detallados:
            import json
            cambios_json = json.dumps(cambios_detallados, default=str)  # default=str para manejar Decimal, datetime, etc.
        
        nuevo_log = Log(
            Usuarioid=usuario_obj,
            correoElectronico=usuario_obj.correo,
            accion=accion_str,
            iddocumento=documento_afectado,
            usuario_afectado=usuario_afectado,
            cambios_detallados=cambios_json,
            hash_archivo_csv=hash_archivo_csv
        )
        nuevo_log.save()
        print(f"Log guardado correctamente: {accion_str} por {usuario_obj.correo}")
    except Exception as e:
        print(f"¡¡ADVERTENCIA!! Falló al guardar el log: {e}")



# =====================================================================
# VISTAS DE NAVEGACIÓN Y AUTENTICACIÓN
# Vistas que manejan la navegación y autenticación del usuario.
# Manejan el login, logout, home, etc.
# =====================================================================

def listar_usuarios(request):
    """
    Vista para listar todos los usuarios del sistema.
    
    Argumentos:
        request: Objeto HttpRequest de Django
        
    Returns (lo que devuelve la funcion):
        HttpResponse: Renderiza el template listar.html con la lista de usuarios
    """
    todos_los_usuarios = usuarios.objects.all()
    return render(request, 'prueba/listar.html', {'usuarios': todos_los_usuarios})



# =====================================================================
# VISTAS DE INICIO DE SESIÓN
# =====================================================================

def login_view(request):
    """
    Vista para el inicio de sesión de usuarios.
    
    Flujo:
    1. Si el usuario ya está autenticado (tiene sesión), redirige a home
    2. Si es GET, muestra el formulario de login (login.html) con get se refiere a la forma en que se envía la información al servidor
    3. Si es POST, valida credenciales y crea sesión si son correctas (POST se refiere a la forma en que se envía la información al servidor)
    
    Argumentos:
        request: Objeto HttpRequest de Django
        
    Returns (lo que devuelve la funcion):
        HttpResponse: Renderiza login.html o redirige a home si las credenciales son correctas
    """
    if 'user_id' in request.session:
        # Si el usuario ya está autenticado (tiene sesión), redirige a home
        return redirect('home')

    # Crear formulario vacío
    form = LoginForm()
    # Inicializar variable de error para mostrar mensajes de error
    error = None # None se refiere a que no hay error

    # Si el método es POST (es post cuando se envía la información al servidor), procesa el formulario
    if request.method == 'POST':
        # Crear formulario con los datos del POST
        form = LoginForm(request.POST)
        # Si el formulario es válido, procesa los datos
        if form.is_valid():
            # Obtener los datos del formulario
            correo_usuario = form.cleaned_data['correo']
            contrasena_usuario = form.cleaned_data['contrasena']

            try: # try se refiere a que se intenta ejecutar el código y si hay un error, se ejecuta el except
                user = usuarios.objects.get(correo=correo_usuario)
                # Verificar contraseña usando bcrypt
                if not _check_password(contrasena_usuario, user.contrasena):
                    user = None
            except usuarios.DoesNotExist:
                user = None

            if user: # Si el usuario existe, crea la sesión
                request.session['user_id'] = str(user.id)
                request.session['user_nombre'] = user.nombre
                return redirect('home')
            else:
                error = "Correo o contraseña incorrectos."
    # Si el formulario no es válido, muestra el formulario con el error
    return render(request, 'prueba/login.html', {'form': form, 'error': error})



# =====================================================================
# VISTAS DE DASHBOARD
# =====================================================================

def home_view(request):
    """
    Vista principal del dashboard (página de inicio).
    
    Funcionalidades:
    - Verifica autenticación del usuario
    - Permite filtrar calificaciones por mercado, origen y período
    - Muestra calificaciones en formato JSON para JavaScript
    
    Argumentos:
        request: Objeto HttpRequest de Django
        
    Returns (lo que devuelve la funcion):
        HttpResponse: Renderiza home.html con las calificaciones filtradas
    """
    # Si el usuario no está autenticado, redirige a login
    if 'user_id' not in request.session:
        return redirect('login')

    try: # try se refiere a que se intenta ejecutar el código y si hay un error, se ejecuta el except
        current_user = usuarios.objects.get(id=request.session['user_id'])
        is_admin = current_user.rol
    except usuarios.DoesNotExist:
        request.session.flush()
        return redirect('login')

    # Si el método es GET, obtiene las calificaciones (get se refiere a la forma en que se envía la información al servidor aqui es get porque se está obteniendo la información del servidor)
    # Inicializar lista de calificaciones
    calificaciones = []
    if request.method == 'GET':
        mercado_raw = request.GET.get('mercado', '')
        # Obtener los datos del formulario
        origen = request.GET.get('origen', '')
        periodo = request.GET.get('periodo', '')
        
        # Normalizar mercado a los valores válidos (acciones, CFI, Fondos mutuos)
        mercado_normalizado = mercado_raw
        if mercado_raw and mercado_raw != 'Todos': # Si el mercado no es Todos, normaliza el mercado
            mercado_lower = mercado_raw.lower().strip()
            if mercado_lower == 'acciones' or mercado_lower == 'accion':
                mercado_normalizado = 'acciones'
            elif mercado_lower == 'cfi':
                mercado_normalizado = 'CFI'
            elif mercado_lower == 'fondos mutuos' or mercado_lower == 'fondosmutuos' or mercado_lower == 'fondo mutuo':
                mercado_normalizado = 'Fondos mutuos'
            else:
                mercado_normalizado = mercado_raw  # Mantener el valor original si no coincide con los valores válidos
        
        # Normalizar origen a los valores válidos (csv, corredor)
        origen_normalizado = origen # Inicializar origen normalizado con normalizar se refiere a que el origen se normaliza a los valores válidos
        if origen:
            origen_lower = origen.lower().strip() # Normalizar origen
            if origen_lower == 'csv': # Si el origen es csv, normaliza el origen
                origen_normalizado = 'csv'
            elif origen_lower == 'corredor': # Si el origen es corredor, normaliza el origen
                origen_normalizado = 'corredor'
        
        query = {} # Inicializar query para la consulta a la base de datos
        if mercado_normalizado and mercado_normalizado != 'Todos': # Si el mercado no es Todos, normaliza el mercado
            query['Mercado'] = mercado_normalizado
        if origen_normalizado: # Si el origen no es None, normaliza el origen
            query['Origen'] = origen_normalizado
        if periodo: # Si el periodo no es None, normaliza el periodo
            try:
                periodo_int = int(periodo) # Convertir el periodo a entero
                query['Ejercicio'] = periodo_int
            except ValueError: # Si el periodo no es un entero, no normaliza el periodo
                pass
        
        # Cargar calificaciones según los filtros aplicados
        # Si hay filtros en query, cargar solo las calificaciones que cumplen con los filtros
        # Si no hay filtros (query vacío), cargar TODAS las calificaciones para que el dashboard no aparezca vacío al inicio
        if query:
            # Aplicar filtros: cargar solo las calificaciones que cumplen con los filtros especificados
            # Ordenar por fecha de actualización descendente (más recientes primero)
            calificaciones = Calificacion.objects(**query).order_by('-FechaAct')
        else:
            # Si no hay filtros, cargar TODAS las calificaciones guardadas
            # Ordenar por fecha de actualización descendente (más recientes primero)
            # Esto asegura que el dashboard muestre todas las calificaciones al cargar la página por primera vez
            calificaciones = Calificacion.objects().order_by('-FechaAct')

    # Serializar calificaciones a formato JSON para el JavaScript (mismo formato que buscar_calificaciones_view)
    import json # Importar json para serializar las calificaciones a formato JSON
    calificaciones_data = [] # Inicializar lista de calificaciones
    for cal in calificaciones:
        # Asegurar que el ID esté disponible
        cal_id = str(cal.id) if cal.id else '' # Convertir el ID a string
        if not cal_id:
            continue  # Saltar calificaciones sin ID (si el ID es None, se salta la calificación)
        
        #diccionario de calificación con los datos de la calificación
        cal_data = {
            'id': cal_id,
            'ejercicio': cal.Ejercicio or '',
            'instrumento': cal.Instrumento or '',
            'fecha_pago': cal.FechaPago.strftime('%Y-%m-%d') if cal.FechaPago else '',
            'descripcion': cal.Descripcion or '',
            'secuencia_evento': cal.SecuenciaEvento or '',
            'fecha_act': cal.FechaAct.strftime('%Y-%m-%d %H:%M:%S') if cal.FechaAct else '',
            'mercado': cal.Mercado or '',
            'origen': cal.Origen or '',
            'factores': {} # Inicializar diccionario de factores
        }
        
        # Agregar todos los factores
        for i in range(8, 38): # range(8, 38) se refiere a que se agregan los factores F8 a F37
            field_name = f'Factor{i:02d}'
            valor = getattr(cal, field_name, 0.0) # getattr se refiere a que se obtiene el valor del campo field_name de la calificación
            cal_data['factores'][field_name] = str(valor) if valor else '0.0' #convertimos a string el valor del factor
        
        calificaciones_data.append(cal_data) # Agregar la calificación al diccionario de calificaciones
    
    calificaciones_json = json.dumps(calificaciones_data) #convertimos a json el diccionario de calificaciones
    
    return render(request, 'prueba/home.html', { #renderizamos el template home.html con los datos de la calificación
        'user_nombre': current_user.nombre, #nombre del usuario
        'is_admin': is_admin, #rol del usuario
        'current_user': current_user, #usuario actual
        'calificaciones': calificaciones, #calificaciones
        'calificaciones_json': calificaciones_json #calificaciones en formato json
    })


# =====================================================================
# VISTAS DE BUSCAR CALIFICACIONES
# =====================================================================

@require_GET # require_GET se refiere a que la vista solo permite GET (get se refiere a la forma en que se envía la información al servidor aqui es get porque se está obteniendo la información del servidor)
def buscar_calificaciones_view(request):
    """
    Vista AJAX para buscar calificaciones según filtros. ajax significa que es una vista que se ejecuta en el navegador y no en el servidor.
    
    Permite filtrar por:
    - Mercado (acciones, CFI, Fondos mutuos)
    - Origen (csv, corredor)
    - Período (año)
    
    Retorna resultados en formato JSON para JavaScript.
    
    Argumentos:
        request: Objeto HttpRequest de Django (solo GET permitido)
        
    Returns (lo que devuelve la funcion):
        JsonResponse: JSON con lista de calificaciones encontradas
    """

    if 'user_id' not in request.session: # Si el usuario no está autenticado, redirige a login
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        mercado_raw = request.GET.get('mercado', '').strip() # Obtener el mercado del formulario
        origen = request.GET.get('origen', '').strip() # Obtener el origen del formulario
        periodo = request.GET.get('periodo', '').strip() # Obtener el periodo del formulario

        # Normalizar mercado a los valores válidos (acciones, CFI, Fondos mutuos)
        mercado_normalizado = mercado_raw # Inicializar mercado normalizado
        if mercado_raw: # Si el mercado no es None, normaliza el mercado
            mercado_lower = mercado_raw.lower().strip() # Normalizar el mercado
            if mercado_lower == 'acciones' or mercado_lower == 'accion': # Si el mercado es acciones, normaliza el mercado
                mercado_normalizado = 'acciones'
            elif mercado_lower == 'cfi': # Si el mercado es CFI, normaliza el mercado
                mercado_normalizado = 'CFI'
            elif mercado_lower == 'fondos mutuos' or mercado_lower == 'fondosmutuos' or mercado_lower == 'fondo mutuo': # Si el mercado es Fondos mutuos, normaliza el mercado
                mercado_normalizado = 'Fondos mutuos'

        # Normalizar origen a los valores válidos (csv, corredor)
        origen_normalizado = origen # Inicializar origen normalizado
        if origen:
            origen_lower = origen.lower().strip() # Normalizar el origen
            if origen_lower == 'csv': # Si el origen es csv, normaliza el origen
                origen_normalizado = 'csv'
            elif origen_lower == 'corredor': # Si el origen es corredor, normaliza el origen
                origen_normalizado = 'corredor'
        
        # Construir query de filtrado
        query = {} # Inicializar query para la consulta a la base de datos
        if mercado_normalizado and mercado_normalizado != 'Todos': # Si el mercado no es Todos, normaliza el mercado
            query['Mercado'] = mercado_normalizado # Agregar el mercado a la query
        if origen_normalizado:
            query['Origen'] = origen_normalizado # Agregar el origen a la query
        if periodo: # Si el periodo no es None, normaliza el periodo
            try:
                periodo_int = int(periodo) # Convertir el periodo a entero
                query['Ejercicio'] = periodo_int # Agregar el periodo a la query
            except ValueError: # Si el periodo no es un entero, no normaliza el periodo
                pass

        # Buscar calificaciones (si no hay filtros, devolver todas)
        if query:
            calificaciones = Calificacion.objects(**query).order_by('-FechaAct') # Cargar las calificaciones que cumplen con los filtros
        else:
            # Si no hay filtros, devolver todas las calificaciones
            calificaciones = Calificacion.objects().order_by('-FechaAct') # Cargar todas las calificaciones

        # Convertir a formato JSON para el JavaScript (mismo formato que home_view)
        calificaciones_data = [] 
        for cal in calificaciones:
            # Asegurar que el ID esté disponible (si el ID es None, se salta la calificación)
            cal_id = str(cal.id) if cal.id else ''
            if not cal_id:
                print(f"ADVERTENCIA: Calificación sin ID: {cal}") # Si el ID es None, se imprime un mensaje de advertencia
                continue  # Saltar calificaciones sin ID
            
            #diccionario de calificación con los datos de la calificación
            cal_data = {
                'id': cal_id,
                'ejercicio': cal.Ejercicio or '',
                'instrumento': cal.Instrumento or '',
                'fecha_pago': cal.FechaPago.strftime('%Y-%m-%d') if cal.FechaPago else '', 
                'descripcion': cal.Descripcion or '',
                'secuencia_evento': cal.SecuenciaEvento or '',
                'fecha_act': cal.FechaAct.strftime('%Y-%m-%d %H:%M:%S') if cal.FechaAct else '', 
                'mercado': cal.Mercado or '',
                'origen': cal.Origen or '',
                'factores': {}
            }
            
            # Agregar todos los factores 
            for i in range(8, 38): # range(8, 38) se refiere a que se agregan los factores F8 a F37
                field_name = f'Factor{i:02d}' 
                valor = getattr(cal, field_name, 0.0) # getattr se refiere a que se obtiene el valor del campo field_name de la calificación
                cal_data['factores'][field_name] = str(valor) if valor else '0.0' #convertimos a string el valor del factor
            
            calificaciones_data.append(cal_data) # Agregar la calificación al diccionario de calificaciones

        return JsonResponse({ #retornamos el diccionario de calificaciones en formato JSON
            'success': True,
            'calificaciones': calificaciones_data, #calificaciones
            'total': len(calificaciones_data) #total de calificaciones
        })

    except Exception as e: # Si hay un error, se imprime un mensaje de error
        print(f"Error al buscar calificaciones: {e}") # Si hay un error, se imprime un mensaje de error
        return JsonResponse({'success': False, 'error': f'Error al buscar: {str(e)}'}, status=500) #retornamos el error en formato JSON


# =====================================================================
# VISTAS DE CERRAR SESIÓN
# =====================================================================

def logout_view(request):
    """
    Vista para cerrar sesión del usuario.
    
    Elimina todos los datos de la sesión y redirige al login.
    
    Argumentos:
        request: Objeto HttpRequest de Django
        
    Returns (lo que devuelve la funcion):
        HttpResponseRedirect: Redirige a la página de login
    """
    request.session.flush() #elimina todos los datos de la sesión
    return redirect('login') #redirige a la página de login


# =====================================================================
# VISTAS DE CALIFICACIONES
# =====================================================================

def ingresar_view(request):
    """
    Vista para ingresar una nueva calificación o modificar una existente.
    
    Flujo:
    1. Si es POST: Valida y guarda/actualiza la calificación
    2. Si es GET: Muestra el formulario vacío o con datos iniciales
    
    Esta vista maneja el primer modal (datos básicos de la calificación).
    Después de guardar, se abre un segundo modal para ingresar factores.
    
    Argumentos:
        request: Objeto HttpRequest de Django
        
    Returns (lo que devuelve la funcion):
        JsonResponse: Si es POST y éxito, retorna JSON con el ID de la calificación
        HttpResponse: Si es GET, renderiza el formulario
    """
    # Si el usuario no está autenticado, redirige a login
    if 'user_id' not in request.session:
        return redirect('login')

    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
    except usuarios.DoesNotExist: # Si el usuario no existe, elimina todos los datos de la sesión y redirige a login
        request.session.flush()
        return redirect('login')

    if request.method == 'POST': # Si el método es POST, procesa el formulario
        form = CalificacionModalForm(request.POST)
        if form.is_valid(): # Si el formulario es válido, procesa los datos
            # Convertir FechaPago de string a DateTime si viene como string
            cleaned_data = form.cleaned_data.copy() # Copia los datos del formulario
            if 'FechaPago' in cleaned_data and cleaned_data['FechaPago']:
                if isinstance(cleaned_data['FechaPago'], str): # Si el campo FechaPago es un string, convierte a DateTime
                    from datetime import datetime # Importamos datetime para convertir a DateTime
                    try:
                        cleaned_data['FechaPago'] = datetime.strptime(cleaned_data['FechaPago'], '%Y-%m-%d') # Convierte a DateTime
                    except: # Si hay un error, pasa al siguiente campo
                        pass
            
            # Validar que SecuenciaEvento sea mayor a 10000 (si la secuencia de evento es menor a 10,000, retorna un error)
            if 'SecuenciaEvento' in cleaned_data and cleaned_data['SecuenciaEvento']:
                if cleaned_data['SecuenciaEvento'] <= 10000: # Si la secuencia de evento es menor a 10,000, retorna un error
                    return JsonResponse({'success': False, 'error': 'La secuencia de evento debe ser mayor a 10,000.'}, status=400)
            
            # Normalizar mercado antes de guardar
            mercado_raw = cleaned_data.get('Mercado', '') # Obtiene el mercado del formulario
            if mercado_raw:
                mercado_lower = mercado_raw.lower().strip() # Normaliza el mercado      
                if mercado_lower == 'acciones' or mercado_lower == 'accion':
                    cleaned_data['Mercado'] = 'acciones'
                elif mercado_lower == 'cfi': # Si el mercado es CFI, normaliza el mercado
                    cleaned_data['Mercado'] = 'CFI'
                elif mercado_lower == 'fondos mutuos' or mercado_lower == 'fondosmutuos' or mercado_lower == 'fondo mutuo': # Si el mercado es Fondos mutuos, normaliza el mercado
                    cleaned_data['Mercado'] = 'Fondos mutuos'
            
            # Normalizar origen antes de guardar
            origen_raw = cleaned_data.get('Origen', 'corredor') # Obtiene el origen del formulario
            if origen_raw:
                origen_lower = origen_raw.lower().strip() # Normaliza el origen
                if origen_lower == 'csv':
                    cleaned_data['Origen'] = 'csv'
                elif origen_lower == 'corredor' or origen_lower == 'manual': # Si el origen es manual, normaliza el origen
                    cleaned_data['Origen'] = 'corredor'
            else:
                cleaned_data['Origen'] = 'corredor'  # Valor por defecto
            
            # Verificar si es una actualización o creación (si el ID de la calificación no es None, actualiza la calificación existente, si el ID de la calificación es None, crea una nueva calificación)
            calificacion_id = request.POST.get('calificacion_id') # Obtiene el ID de la calificación del formulario
            if calificacion_id: # Si el ID de la calificación no es None, actualiza la calificación existente
                # Actualizar calificación existente
                try:
                    calificacion = Calificacion.objects.get(id=calificacion_id) # Obtiene la calificación existente
                    # Capturar cambios antes de actualizar
                    cambios_detallados = [] # Inicializar lista de cambios detallados
                    campos_actualizados = False # Inicializar flag de campos actualizados
                    
                    for key, value in cleaned_data.items(): # Recorrer los campos del formulario
                        # Verificar si el campo fue enviado en el POST original
                        if key in request.POST: # Si el campo fue enviado en el POST original (si el campo fue enviado en el POST original, se actualiza el campo)
                            # Obtener valor actual antes de modificar
                            valor_actual = getattr(calificacion, key, None) # Obtiene el valor actual del campo
                            
                            # Formatear valores para comparación y visualización
                            def formatear_valor(val): # Formatea el valor para comparación y visualización
                                if val is None:
                                    return None
                                if isinstance(val, datetime.datetime): # Si el valor es un datetime, convierte a string
                                    return val.strftime('%Y-%m-%d %H:%M:%S')
                                if isinstance(val, bool): # Si el valor es un booleano, convierte a string
                                    return 'Sí' if val else 'No'
                                return str(val)
                            
                            valor_anterior_str = formatear_valor(valor_actual) # Formatea el valor anterior para comparación y visualización
                            valor_nuevo_str = formatear_valor(value) # Formatea el valor nuevo para comparación y visualización
                            
                            # Solo actualizar si el valor es diferente del actual (si el valor es diferente del actual, se actualiza el campo)
                            cambio_realizado = False
                            
                            # Para campos booleanos, comparar directamente
                            if isinstance(value, bool): # Si el valor es un booleano, compara directamente
                                if valor_actual != value: # Si el valor es diferente del actual, se actualiza el campo
                                    setattr(calificacion, key, value) # Actualiza el campo
                                    campos_actualizados = True # Se actualiza el flag de campos actualizados
                                    cambio_realizado = True # Se actualiza el flag de cambio realizado (si el valor es diferente del actual, se actualiza el campo)
                            # Para campos numéricos, comparar valores
                            elif isinstance(value, (int, float)): # Si el valor es un int o float, compara directamente
                                if valor_actual != value: # Si el valor es diferente del actual, se actualiza el campo
                                    setattr(calificacion, key, value) # Actualiza el campo
                                    campos_actualizados = True # Se actualiza el flag de campos actualizados
                                    cambio_realizado = True # Se actualiza el flag de cambio realizado (si el valor es diferente del actual, se actualiza el campo)
                            # Para strings, actualizar si no está vacío y es diferente
                            elif isinstance(value, str): # Si el valor es un string, compara directamente
                                if value.strip() != '' and valor_actual != value: # Si el valor es diferente del actual, se actualiza el campo
                                    setattr(calificacion, key, value) # Actualiza el campo
                                    campos_actualizados = True # Se actualiza el flag de campos actualizados
                                    cambio_realizado = True # Se actualiza el flag de cambio realizado (si el valor es diferente del actual, se actualiza el campo)
                            # Para fechas y otros tipos, comparar si no es None
                            elif value is not None: # Si el valor no es None, compara directamente
                                if valor_actual != value: # Si el valor es diferente del actual, se actualiza el campo
                                    setattr(calificacion, key, value) # Actualiza el campo
                                    campos_actualizados = True # Se actualiza el flag de campos actualizados
                                    cambio_realizado = True # Se actualiza el flag de cambio realizado (si el valor es diferente del actual, se actualiza el campo)
                            
                            # Si hubo cambio, agregar a la lista de cambios (si el valor es diferente del actual, se actualiza el campo)
                            if cambio_realizado:
                                cambios_detallados.append({ # Agregar el cambio a la lista de cambios
                                    'campo': key, # Campo que se actualizó
                                    'valor_anterior': valor_anterior_str, # Valor anterior para comparación y visualización
                                    'valor_nuevo': valor_nuevo_str # Valor nuevo para comparación y visualización
                                })
                    
                    # Si EventoCapital está vacío y SecuenciaEvento tiene valor, asignar EventoCapital = SecuenciaEvento
                    if (not calificacion.EventoCapital or calificacion.EventoCapital == '') and calificacion.SecuenciaEvento:
                        calificacion.EventoCapital = str(calificacion.SecuenciaEvento)
                        if not campos_actualizados:
                            campos_actualizados = True
                    
                    # Actualizar fecha de modificación solo si realmente se modificó algo
                    if campos_actualizados:
                        calificacion.FechaAct = datetime.datetime.now() # Actualiza la fecha de modificación
                        calificacion.save()
                        _crear_log(current_user, 'Modificar Calificacion', documento_afectado=calificacion, cambios_detallados=cambios_detallados if cambios_detallados else None)
                    else: # Si no hubo cambios, no se actualiza la fecha de modificación y se crea un log de modificación sin cambios
                        _crear_log(current_user, 'Modificar Calificacion', documento_afectado=calificacion)
                    return JsonResponse({ #retornamos el diccionario de calificaciones en formato JSON
                        'success': True,
                        'calificacion_id': str(calificacion.id), #ID de la calificación
                        'data': { #datos de la calificación
                            'mercado': calificacion.Mercado or '', #mercado de la calificación
                            'origen': calificacion.Origen or '', #origen de la calificación
                            'instrumento': calificacion.Instrumento or '', #instrumento de la calificación
                            'evento_capital': calificacion.EventoCapital or str(calificacion.SecuenciaEvento) if calificacion.SecuenciaEvento else '', #evento capital de la calificación (usa secuencia si está vacío)
                            'fecha_pago': calificacion.FechaPago.strftime('%Y-%m-%d') if calificacion.FechaPago else '', #fecha de pago de la calificación
                            'secuencia': calificacion.SecuenciaEvento or '', #secuencia de evento de la calificación
                            'anho': calificacion.Anho or calificacion.Ejercicio or '', #año de la calificación
                            'valor_historico': str(calificacion.ValorHistorico or 0.0), #valor histórico de la calificación
                            'descripcion': calificacion.Descripcion or '' #descripción de la calificación
                        }
                    })
                except Calificacion.DoesNotExist: # Si la calificación no existe, retorna un error
                    return JsonResponse({'success': False, 'error': 'Calificación no encontrada.'}, status=404) 
            else:
                # Crear nueva calificación
                nueva_calificacion = Calificacion(**cleaned_data) # Crea una nueva calificación con los datos del formulario
                # Asignar EventoCapital con el valor de SecuenciaEvento si EventoCapital no está definido
                if not nueva_calificacion.EventoCapital and nueva_calificacion.SecuenciaEvento:
                    nueva_calificacion.EventoCapital = str(nueva_calificacion.SecuenciaEvento)
                nueva_calificacion.save() # Guarda la nueva calificación
                _crear_log(current_user, 'Crear Calificacion', documento_afectado=nueva_calificacion) # Crea un log de creación de la calificación
                # Retornar JSON con el ID de la calificación para abrir el segundo modal (si la calificación se creó exitosamente, se retorna el ID de la calificación para abrir el segundo modal)
                return JsonResponse({ #retornamos el diccionario de calificaciones en formato JSON
                    'success': True,
                    'calificacion_id': str(nueva_calificacion.id), #ID de la calificación
                    'data': { #datos de la calificación
                        'mercado': nueva_calificacion.Mercado or '', #mercado de la calificación
                        'origen': nueva_calificacion.Origen or '', #origen de la calificación
                        'instrumento': nueva_calificacion.Instrumento or '', #instrumento de la calificación
                        'evento_capital': nueva_calificacion.EventoCapital or str(nueva_calificacion.SecuenciaEvento) if nueva_calificacion.SecuenciaEvento else '', #evento capital de la calificación (usa secuencia si está vacío)
                        'fecha_pago': nueva_calificacion.FechaPago.strftime('%Y-%m-%d') if nueva_calificacion.FechaPago else '', #fecha de pago de la calificación
                        'secuencia': nueva_calificacion.SecuenciaEvento or '', #secuencia de evento de la calificación
                        'anho': nueva_calificacion.Anho or nueva_calificacion.Ejercicio or '', #año de la calificación
                        'valor_historico': str(nueva_calificacion.ValorHistorico or 0.0), #valor histórico de la calificación
                        'descripcion': nueva_calificacion.Descripcion or '' #descripción de la calificación
                    }
                })
        else:
            return JsonResponse({'success': False, 'error': form.errors.as_json()}, status=400) # Si el formulario no es válido, retorna un error
    else:
        initial_data = { #datos iniciales del formulario
            'Mercado': request.GET.get('mercado'), #mercado del formulario
            'Ejercicio': request.GET.get('ejercicio'), #ejercicio del formulario
            'Instrumento': request.GET.get('instrumento'), #instrumento del formulario
            'FechaPago': request.GET.get('fecha_pago'), #fecha de pago del formulario
            'SecuenciaEvento': request.GET.get('secuencia'), #secuencia de evento del formulario
        }
        form = CalificacionModalForm(initial=initial_data) # Crea un formulario con los datos iniciales

    return render(request, 'prueba/ingresar.html', {'form': form}) # Renderiza el formulario en la página ingresar.html


# =====================================================================
# VISTAS DE INGRESAR CALIFICACIONES CON MONTOS
# =====================================================================

def ingresar_calificacion(request):
    """
    Vista para ingresar calificaciones con MONTOS.
    
    El usuario ingresa montos (dinero), y el sistema calcula los factores automáticamente.
    Según los requisitos: todos los factores (8-37) se calculan dividiendo cada monto por la Suma Base (suma de montos 8-19).
    
    Flujo:
    1. Usuario ingresa montos del 8 al 37
    2. Sistema calcula SumaBase = suma de montos 8-19
    3. Sistema calcula cada Factor = Monto / SumaBase
    4. Sistema guarda calificación con factores calculados
    
    Argumentos:
        request: Objeto HttpRequest de Django
        
    Returns (lo que devuelve la funcion):
        HttpResponseRedirect: Redirige a home si se guardó exitosamente
        HttpResponse: Renderiza el formulario si es GET o hay errores
    """
    if 'user_id' not in request.session: # Si el usuario no está autenticado, redirige a login
        return redirect('login')
    
    try:
        current_user = usuarios.objects.get(id=request.session['user_id']) # Obtiene el usuario autenticado
    except usuarios.DoesNotExist:
        request.session.flush() # Elimina todos los datos de la sesión y redirige a login
        return redirect('login')
    
    if request.method == 'POST': # Si el método es POST, procesa el formulario
        form = MontosForm(request.POST) # Crea un formulario con los datos del POST
        
        if form.is_valid(): # Si el formulario es válido, procesa los datos
            try:
                from decimal import Decimal # Importamos decimal para manejar los montos
                
                # Obtener todos los montos del formulario (como objetos Decimal)
                montos = {} # Inicializar diccionario de montos
                for i in range(8, 38): # Del 8 al 37 (30 montos)
                    monto_key = f'monto_{i}' # Clave del monto con clave del monto se refiere a la clave del monto en el formulario (monto_8, monto_9, etc.)
                    monto_value = form.cleaned_data.get(monto_key, Decimal(0)) # Obtiene el valor del monto (si el valor no existe, se asigna 0)
                    # Convertir a Decimal si no lo es (si el valor no es un Decimal, convierte a Decimal) (si el valor no es un Decimal, convierte a Decimal)
                    if not isinstance(monto_value, Decimal): #conversion a Decimal
                        montos[i] = Decimal(str(monto_value)) if monto_value else Decimal(0) # Si el valor no es un Decimal, convierte a Decimal
                    else:
                        montos[i] = monto_value # Si el valor es un Decimal, lo asigna al diccionario de montos
                
                #Calcular la Suma Base (suma de montos del 8 al 19)
                suma_base = Decimal(0) # Inicializar la suma base en 0
                for i in range(8, 20):  # Del 8 al 19 inclusive
                    suma_base += montos.get(i, Decimal(0)) # Suma el monto al total de la suma base
                
                # Crear el objeto Calificacion para GUARDAR
                nueva_calificacion = Calificacion() # Crea un nuevo objeto Calificacion
                
                # Asignar los datos generales (usando nombres correctos del modelo)
                nueva_calificacion.Ejercicio = form.cleaned_data.get('Ejercicio') 
                
                # Normalizar mercado antes de guardar
                mercado_raw = form.cleaned_data.get('Mercado', '') # Obtiene el mercado del formulario
                mercado_normalizado = mercado_raw # Normaliza el mercado    
                if mercado_raw:
                    mercado_lower = mercado_raw.lower().strip() # Normaliza el mercado
                    if mercado_lower == 'acciones' or mercado_lower == 'accion': # Si el mercado es acciones, normaliza el mercado
                        mercado_normalizado = 'acciones'
                    elif mercado_lower == 'cfi': # Si el mercado es CFI, normaliza el mercado
                        mercado_normalizado = 'CFI'
                    elif mercado_lower == 'fondos mutuos' or mercado_lower == 'fondosmutuos' or mercado_lower == 'fondo mutuo': # Si el mercado es Fondos mutuos, normaliza el mercado
                        mercado_normalizado = 'Fondos mutuos'
                
                # Asignar el mercado normalizado a la calificación
                nueva_calificacion.Mercado = mercado_normalizado # Asigna el mercado normalizado a la calificación
                nueva_calificacion.Instrumento = form.cleaned_data.get('Instrumento', '') # Asigna el instrumento a la calificación
                
                # Normalizar origen antes de guardar
                origen_raw = form.cleaned_data.get('Origen', 'corredor') # Obtiene el origen del formulario
                origen_normalizado = origen_raw # Normaliza el origen
                if origen_raw:
                    origen_lower = origen_raw.lower().strip() # Normaliza el origen
                    if origen_lower == 'csv': # Si el origen es CSV, normaliza el origen
                        origen_normalizado = 'csv'
                    elif origen_lower == 'corredor' or origen_lower == 'manual': # Si el origen es manual, normaliza el origen
                        origen_normalizado = 'corredor'
                
                nueva_calificacion.Origen = origen_normalizado # Asigna el origen normalizado a la calificación
                
                # Calcular y asignar cada FACTOR (Factores del 8 al 37)
                # El requisito dice "Decimal redondeado al 8vo decimal" 
                EIGHT_PLACES = Decimal('0.00000001') # 8 decimales
                
                if suma_base > 0: # Si la suma base es mayor a 0, calcular todos los factores
                    # Calcular TODOS los factores (del 8 al 37) dividiendo cada monto por la Suma Base
                    for i in range(8, 38): # Del 8 al 37
                        factor_field = f'Factor{i:02d}'  # Factor08, Factor09, etc.
                        monto = montos.get(i, Decimal(0)) # Obtiene el monto
                        factor_calculado = (monto / suma_base).quantize(EIGHT_PLACES) # Calcula el factor
                        setattr(nueva_calificacion, factor_field, factor_calculado) # Asigna el factor a la calificación
                else: # Si la suma base es 0, todos los factores son 0
                    # Si la suma es 0, todos los factores son 0
                    for i in range(8, 38):
                        factor_field = f'Factor{i:02d}'
                        setattr(nueva_calificacion, factor_field, Decimal(0))
                
                # Guardar el objeto con los factores CALCULADOS (guarda la calificación con los factores calculados)
                nueva_calificacion.save()
                
                # Crear el Log (crea un log de creación de la calificación)
                _crear_log(
                    current_user,
                    'Crear Calificacion',
                    documento_afectado=nueva_calificacion
                )
                
                messages.success(request, '¡Calificación ingresada y calculada con éxito!') # Muestra un mensaje de éxito
                return redirect('home') # Redirige a la página home
                
            except Exception as e:
                print(f"Error al calcular factores: {e}")
                messages.error(request, f'Error al calcular: {str(e)}')
        else:
            # Si el formulario no es válido, mostrar errores
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = MontosForm()  # Crear un formulario vacío
    
    # Renderizar la plantilla del modal con el formulario de MONTOS
    return render(request, 'prueba/modal_ingreso.html', {'form': form})


# =====================================================================
# VISTAS DE GUARDAR FACTORES (Vista para guardar los factores calculados en la calificación)
# =====================================================================

@require_POST
def guardar_factores_view(request):
    """
    Vista para guardar los factores calculados en la calificación
    
    Argumentos:
        request: Objeto HttpRequest de Django
        
    Returns (lo que devuelve la funcion):
        JsonResponse: JSON con el resultado de la operación
    """
    if 'user_id' not in request.session: # Si el usuario no está autenticado, retorna un error
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401) # Si el usuario no existe, retorna un error

    calificacion_id = request.POST.get('calificacion_id') # Obtiene el ID de la calificación
    if not calificacion_id:
        return JsonResponse({'success': False, 'error': 'Falta calificacion_id'}, status=400) # Si no hay ID de la calificación, retorna un error

    try: 
        calificacion = Calificacion.objects.get(id=calificacion_id) # Obtiene la calificación
    except Calificacion.DoesNotExist: 
        return JsonResponse({'success': False, 'error': 'Calificación no encontrada'}, status=404) # Si la calificación no existe, retorna un error

    try:
        from decimal import Decimal # Importamos decimal para manejar los factores
        
        # Los factores ya fueron calculados y están en el formulario
        # IMPORTANTE: Los montos ya fueron guardados cuando se calcularon los factores
        # No debemos sobrescribir los montos aquí, solo guardar los factores calculados
        # Actualizar solo los factores que fueron enviados en el POST

        cambios_detallados = [] # Inicializar lista de cambios detallados
        factores_actualizados = False # Inicializar flag de factores actualizados
        for i in range(8, 38):
            factor_field = f'Factor{i:02d}' # Clave del factor con clave del factor se refiere a la clave del factor en el formulario (Factor08, Factor09, etc.)
            valor_post = request.POST.get(factor_field)
            # Solo actualizar si el valor fue enviado (no None)
            if valor_post is not None: 
                try:
                    valor_decimal = Decimal(str(valor_post)) if valor_post else Decimal(0) # Convertir el valor a Decimal
                    # Solo actualizar si el valor es diferente al actual
                    valor_actual = getattr(calificacion, factor_field, Decimal(0)) # Obtiene el valor actual del factor
                    if valor_decimal != valor_actual: # Si el valor es diferente al actual, se actualiza el factor
                        cambios_detallados.append({ # Agregar el cambio a la lista de cambios detallados
                            'campo': factor_field, # Campo que se actualizó
                            'valor_anterior': str(valor_actual), # Valor anterior para comparación y visualización
                            'valor_nuevo': str(valor_decimal) # Valor nuevo para comparación y visualización
                        })
                        setattr(calificacion, factor_field, valor_decimal) # Asigna el valor actualizado al factor
                        factores_actualizados = True # Se actualiza el flag de factores actualizados
                except (ValueError, TypeError):
                    # Si hay error, mantener el valor actual
                    pass # Si hay error, se mantiene el valor actual
        
        
        # Solo guardar los factores calculados
        # Actualizar la fecha de modificación solo si se actualizaron factores
        if factores_actualizados: # Si se actualizaron factores, se actualiza la fecha de modificación
            calificacion.FechaAct = datetime.datetime.now() # Actualiza la fecha de modificación
            calificacion.save() # Guarda la calificación
            _crear_log(current_user, 'Modificar Calificacion', documento_afectado=calificacion, cambios_detallados=cambios_detallados if cambios_detallados else None)
        else:
            _crear_log(current_user, 'Modificar Calificacion', documento_afectado=calificacion)
        return JsonResponse({'success': True})
    except Exception as e:
        print(f"Error al guardar factores: {e}")
        return JsonResponse({'success': False, 'error': f'Error al guardar: {str(e)}'}, status=500)


# =====================================================================
# VISTAS DE FACTORES Y MONTOS (CÁLCULOS)
# =====================================================================

@require_POST
def calcular_factores_view(request):
    """
    Vista AJAX para calcular factores desde MONTOS ingresados. (ajax es una técnica que permite realizar peticiones a un servidor sin recargar la página.)
    
    El usuario ingresa montos, y esta vista calcula los factores:
    - SumaBase = suma de montos del 8 al 19 (suma de montos del 8 al 19)
    - Factor = Monto / SumaBase para cada monto del 8 al 37 (factor = monto / suma base para cada monto del 8 al 37)
    
    No guarda los factores, solo los calcula y los retorna para previsualización. (no guarda los factores, solo los calcula y los retorna para previsualización)
    
    Argumentos:
        request: Objeto HttpRequest de Django (solo POST permitido)
        
    Returns (lo que devuelve la funcion):
        JsonResponse: JSON con factores calculados para mostrar al usuario
    """
    if 'user_id' not in request.session: # Si el usuario no está autenticado, retorna un error
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        current_user = usuarios.objects.get(id=request.session['user_id']) # Obtiene el usuario autenticado
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401) # Si el usuario no existe, retorna un error

    calificacion_id = request.POST.get('calificacion_id') # Obtiene el ID de la calificación
    if not calificacion_id:
        return JsonResponse({'success': False, 'error': 'Falta calificacion_id'}, status=400) # Si no hay ID de la calificación, retorna un error

    try:
        calificacion = Calificacion.objects.get(id=calificacion_id) # Obtiene la calificación
    except Calificacion.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Calificación no encontrada'}, status=404) # Si la calificación no existe, retorna un error

    try:
        from decimal import Decimal # Importamos decimal para manejar los montos
        
        #  Obtener todos los MONTOS del formulario (el usuario ingresa montos)
        montos = {} # Inicializar diccionario de montos
        for i in range(8, 38): # Del 8 al 37
            monto_key = f'monto_{i}' # Clave del monto con clave del monto se refiere a la clave del monto en el formulario (monto_8, monto_9, etc.)
            valor_post = request.POST.get(monto_key, '0.00') # Obtiene el valor del monto
            try:
                montos[i] = Decimal(str(valor_post)) if valor_post else Decimal(0) # Convertir el valor a Decimal
            except (ValueError, TypeError):
                montos[i] = Decimal(0) # Si hay error, se asigna 0

        #  Calcular la Suma Base (suma de montos del 8 al 19)
        suma_base = Decimal(0) # Inicializar la suma base en 0
        for i in range(8, 20):  # Del 8 al 19 inclusive
            suma_base += montos.get(i, Decimal(0))

        #  Guardar solo los montos que fueron enviados y son diferentes de 0
        # Si un monto no se envía o es 0, mantener el valor actual

        cambios_detallados = [] # Inicializar lista de cambios detallados
        montos_actualizados = False 
        for i in range(8, 38):
            monto_field = f'Monto{i:02d}' # Clave del monto con clave del monto se refiere a la clave del monto en el formulario (Monto08, Monto09, etc.)
            monto_value = montos.get(i, Decimal(0)) 
            # Solo actualizar si el monto fue enviado y es diferente del actual
            valor_actual = getattr(calificacion, monto_field, Decimal(0)) 
            if monto_value != valor_actual: # Si el monto es diferente al actual, se actualiza el monto
                cambios_detallados.append({ # Agregar el cambio a la lista de cambios detallados
                    'campo': monto_field, # Campo que se actualizó
                    'valor_anterior': str(valor_actual), # Valor anterior para comparación y visualización
                    'valor_nuevo': str(monto_value) # Valor nuevo para comparación y visualización
                })
                setattr(calificacion, monto_field, monto_value) # Asigna el valor actualizado al monto
                montos_actualizados = True # Se actualiza el flag de montos actualizados
        
        # Guardar la suma base para poder hacer el cálculo inverso después 
        # Solo actualizar si cambió
        suma_base_actual = getattr(calificacion, 'SumaBase', Decimal(0)) # Obtiene el valor actual de la suma base
        if suma_base != suma_base_actual: # Si la suma base es diferente al actual, se actualiza la suma base
            cambios_detallados.append({
                'campo': 'SumaBase', # Campo que se actualizó
                'valor_anterior': str(suma_base_actual), # Valor anterior para comparación y visualización
                'valor_nuevo': str(suma_base) # Valor nuevo para comparación y visualización
            })
            calificacion.SumaBase = suma_base # Asigna el valor actualizado a la suma base
            montos_actualizados = True # Se actualiza el flag de montos actualizados
        
        # Actualizar la fecha de modificación solo si se actualizaron montos
        if montos_actualizados:
            calificacion.FechaAct = datetime.datetime.now()
            calificacion.save()
            # Guardar log con cambios detallados
            _crear_log(current_user, 'Modificar Calificacion', documento_afectado=calificacion, cambios_detallados=cambios_detallados if cambios_detallados else None)
        
        # Calcular todos los factores (8-37) dividiendo cada monto por la Suma Base
        EIGHT_PLACES = Decimal('0.00000001') # 8 decimales se usa eight places para tener 8 decimales
        factores_calculados = {} # Inicializar diccionario de factores calculados
        
        if suma_base > 0: # Si la suma base es mayor a 0, calcular todos los factores
            for i in range(8, 38): # Del 8 al 37
                monto = montos.get(i, Decimal(0)) # Obtiene el monto
                factor_calculado = (monto / suma_base).quantize(EIGHT_PLACES) # Calcula el factor se usa quantize para redondear el factor a 8 decimales
                factor_field = f'Factor{i:02d}' # Clave del factor con clave del factor se refiere a la clave del factor en el formulario (Factor08, Factor09, etc.)
                factores_calculados[factor_field] = str(factor_calculado) # Asigna el factor calculado al diccionario de factores calculados
        else: # Si la suma base es 0, todos los factores son 0
            # Si la suma es 0, todos los factores son 0
            for i in range(8, 38):
                factor_field = f'Factor{i:02d}' # Clave del factor con clave del factor se refiere a la clave del factor en el formulario (Factor08, Factor09, etc.)
                factores_calculados[factor_field] = '0.00000000' # Asigna 0 a todos los factores

        # Formatear factores para retornar (sin guardar aún, solo mostrar) se usa rstrip para eliminar los ceros innecesarios y el punto decimal si no hay decimales
        factores_formateados = {} # Inicializar diccionario de factores formateados
        for i in range(8, 38): # Del 8 al 37
            factor_field = f'Factor{i:02d}' # Clave del factor con clave del factor se refiere a la clave del factor en el formulario (Factor08, Factor09, etc.)
            valor_str = factores_calculados.get(factor_field, '0.00000000') # Obtiene el valor del factor
            # Formatear eliminando ceros innecesarios
            try:
                valor_float = float(valor_str) # Convierte el valor a float
                factores_formateados[factor_field] = f"{valor_float:.8f}".rstrip('0').rstrip('.') # Formatea el factor a 8 decimales y elimina los ceros innecesarios y el punto decimal si no hay decimales
                if factores_formateados[factor_field] == '': # Si el factor es 0, se asigna 0
                    factores_formateados[factor_field] = '0'
            except (ValueError, TypeError): # Si hay error, se asigna 0
                factores_formateados[factor_field] = '0.0'

        # Información de debug se usa para debuggear esto se ve reflejado en la consola es para test mas que nada xd
        # Crear diccionario con información de debug para diagnóstico y pruebas
        # NO incluir debug_info dentro de sí mismo (eso causaría una referencia circular)
        debug_info = {
            'suma_base': str(suma_base), # Suma base para comparación y visualización
            'factores_calculados': factores_calculados, # Factores calculados para comparación y visualización
            'factores_formateados': factores_formateados # Factores formateados para comparación y visualización
        }

        return JsonResponse({ # Retorna un JSON con los factores calculados, la suma base y la información de debug
            'success': True, # success se refiere a si la operación fue exitosa
            'message': 'Factores calculados exitosamente', # message se refiere al mensaje de éxito
            'factores': factores_formateados, # factores se refiere a los factores calculados
            'suma_base': str(suma_base), # suma_base se refiere a la suma base
            'debug': debug_info # debug se refiere a la información de debug
        })

    except Exception as e: # Si hay error, se retorna un error
        print(f"Error al calcular factores: {e}")
        return JsonResponse({'success': False, 'error': f'Error al calcular: {str(e)}'}, status=500)


# =====================================================================
# VISTAS DE ADMINISTRACIÓN DE USUARIOS
# =====================================================================

def administrar_view(request): 
    """
    Vista para administrar usuarios (solo administradores).
    
    Muestra la lista de todos los usuarios del sistema.
    Permite crear, modificar y eliminar usuarios.
    
    Argumentos:
        request: Objeto HttpRequest de Django
        
    Returns (lo que devuelve la funcion):
        HttpResponseForbidden: Si el usuario no es administrador
        HttpResponse: Renderiza administrar.html con la lista de usuarios
    """
    if 'user_id' not in request.session: # Si el usuario no está autenticado, redirige a login
        return redirect('login')

    try:
        current_user = usuarios.objects.get(id=request.session['user_id']) # Obtiene el usuario autenticado
    except usuarios.DoesNotExist:
        request.session.flush() # Si el usuario no existe, se limpia la sesión
        return redirect('login')

    if not current_user.rol: # Si el usuario no es administrador, se retorna un error
        return HttpResponseForbidden("<h1>Acceso Denegado</h1><p>No tienes permisos...</p><a href='/home/'>Volver</a>") # Se retorna un error de acceso denegado
    
    # Renderiza el template administrar.html con la lista de usuarios
    todos_los_usuarios = usuarios.objects.all() # Obtiene todos los usuarios
    return render(request, 'prueba/administrar.html', {
        'user_nombre': current_user.nombre, # Nombre del usuario
        'lista_usuarios': todos_los_usuarios, # Lista de usuarios
        'is_admin': current_user.rol, # Rol del usuario
        'current_user_id': str(current_user.id) # ID del usuario
    })


# =====================================================================
# VISTAS DE CREAR USUARIO
# =====================================================================

@require_POST
def crear_usuario_view(request):
    """
    Vista AJAX para crear un nuevo usuario (solo administradores). (ajax es una técnica que permite realizar peticiones a un servidor sin recargar la página.)
    
    Valida el formulario, hashea la contraseña y guarda el usuario en MongoDB.
    También maneja la foto de perfil si se proporciona.
    
    Argumentos:
        request: Objeto HttpRequest de Django (solo POST permitido)
        
    Returns (lo que devuelve la funcion):
        JsonResponse: JSON con success=True si se creó exitosamente, o errores si falló
    """
    if 'user_id' not in request.session: # Si el usuario no está autenticado, retorna un error
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        admin_user = usuarios.objects.get(id=request.session['user_id']) # Obtiene el usuario autenticado
        if not admin_user.rol:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403) # Si el usuario no es administrador, retorna un error
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Admin no válido'}, status=401) # Si el usuario no existe, retorna un error

    form = UsuarioForm(request.POST) # Obtiene el formulario el post esta ahi para que el usuario ingrese los datos del formulario
    if form.is_valid(): # Si el formulario es válido, se crea el usuario
        try:
            # Crear usuario con datos del formulario
            cleaned_data = form.cleaned_data.copy() 
            # Eliminar confirmar_contrasena ya que solo es para validación
            cleaned_data.pop('confirmar_contrasena', None) # Eliminar confirmar_contrasena ya que solo es para validación
            # Hashear la contraseña antes de guardar
            if 'contrasena' in cleaned_data and cleaned_data['contrasena']: # Si la contraseña está en el formulario, se hashea la contraseña
                cleaned_data['contrasena'] = _hash_password(cleaned_data['contrasena']) # Hashea la contraseña
            
            nuevo_usuario = usuarios(**cleaned_data) # Crea el usuario con los datos del formulario
            nuevo_usuario.save()  # Guardar primero para obtener el ID
            
            # Manejar foto de perfil si se proporciona se guarda la foto del usuario
            if 'foto_perfil' in request.FILES: # Si se proporciona una foto de perfil, se guarda la foto del usuario
                try:
                    foto_ruta = _guardar_foto_perfil(request.FILES['foto_perfil'], str(nuevo_usuario.id)) # Guarda la foto del usuario
                    nuevo_usuario.foto_perfil = foto_ruta # Asigna la ruta de la foto al usuario esto se hace ya que estamos trabajando de forma local y no en la base de datos
                    nuevo_usuario.save()  # Guardar nuevamente con la foto
                except ValueError as e: # Si hay error, se elimina el usuario y se retorna un error
                    nuevo_usuario.delete()  # Eliminar usuario si falla la foto 
                    return JsonResponse({'success': False, 'error': str(e)}, status=400) # Si hay error, se retorna un error
                except Exception as e: # Si hay error, se elimina el usuario
                    nuevo_usuario.delete()  # Eliminar usuario si falla la foto
                    print(f"Error al guardar foto: {e}") # Si hay error, se imprime el error
                    return JsonResponse({'success': False, 'error': f'Error al guardar foto: {e}'}, status=500) # Si hay error, se retorna un error
        except Exception as e:
            print(f"Error al crear usuario: {e}")
            return JsonResponse({'success': False, 'error': f'Error interno: {e}'}, status=500)
    else:
        return JsonResponse({'success': False, 'error': form.errors.as_json()}, status=400)


# =====================================================================
# VISTAS DE ELIMINAR USUARIOS
# =====================================================================

@require_POST
def eliminar_usuarios_view(request):
    """
    Vista AJAX para eliminar usuarios (solo administradores). (ajax es una técnica que permite realizar peticiones a un servidor sin recargar la página.)
    
    Elimina usuarios de la base de datos.
    
    Argumentos:
        request: Objeto HttpRequest de Django (solo POST permitido)
        
    Returns (lo que devuelve la funcion):
        JsonResponse: JSON con success=True si se eliminó exitosamente, o errores si falló
    """
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401) # Si el usuario no está autenticado, retorna un error

    try:
        admin_user = usuarios.objects.get(id=request.session['user_id']) # Obtiene el usuario autenticado
        if not admin_user.rol:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403) # Si el usuario no es administrador, retorna un error
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Admin no válido'}, status=401) # Si el usuario no existe, retorna un error

    try:
        data = json.loads(request.body) # Obtiene los datos del formulario
        user_ids_to_delete_str = data.get('user_ids', [])  # Son strings (user_ids es el nombre del campo en el formulario)
        if not isinstance(user_ids_to_delete_str, list) or not user_ids_to_delete_str: # Si el usuario no es una lista o no existe, retorna un error
            return JsonResponse({'success': False, 'error': 'Lista de IDs inválida'}, status=400)
    except json.JSONDecodeError: # Si hay error, retorna un error
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400) # Si hay error, retorna un error

    if request.session['user_id'] in user_ids_to_delete_str: # Si el usuario está intentando eliminarse a sí mismo, retorna un error
        return JsonResponse({'success': False, 'error': 'No puedes eliminarte a ti mismo'}, status=400) # Si el usuario está intentando eliminarse a sí mismo, retorna un error

    try:
        # Convertimos los strings del JSON a ObjectIds para la BBDD (ObjectId es un tipo de dato en MongoDB)
        ids_a_eliminar = [ObjectId(uid) for uid in user_ids_to_delete_str] # Convierte los strings del JSON a ObjectIds para la BBDD
    except Exception: # Si hay error, retorna un error
        return JsonResponse({'success': False, 'error': 'Uno o más IDs tienen un formato inválido'}, status=400) # Si hay error, retorna un error

    for user_id in ids_a_eliminar: # Para cada usuario a eliminar, se elimina la foto de perfil y se crea el log
        try:
            # Intentamos obtener el usuario antes de eliminarlo para el log y eliminar su foto
            usuario_eliminado = usuarios.objects.get(id=user_id)
            
            # Eliminar foto de perfil si existe
            if usuario_eliminado.foto_perfil:
                try:
                    foto_path = settings.MEDIA_ROOT / usuario_eliminado.foto_perfil # Obtiene la ruta de la foto de perfil
                    if foto_path.exists():
                        foto_path.unlink() # Elimina la foto de perfil
                        print(f"Foto de perfil eliminada: {foto_path}") # Imprime el mensaje de eliminación de la foto de perfil
                except Exception as e: # Si hay error, retorna un error
                    print(f"Error al eliminar foto de perfil: {e}") # Imprime el error de eliminación de la foto de perfil
            
            _crear_log( # Crea el log de eliminación de usuario
                admin_user, # Usuario que eliminó el usuario
                'Eliminar Usuario', # Accion que se realizó
                usuario_afectado=usuario_eliminado # Usuario afectado por la acción
            )
        except usuarios.DoesNotExist: # Si ya no existe, creamos el log con el ID directamente
            _crear_log( # Crea el log de eliminación de usuario
                admin_user, # Usuario que eliminó el usuario
                'Eliminar Usuario', # Accion que se realizó
                usuario_afectado=user_id # Usuario afectado por la acción
            )
    delete_result = usuarios.objects(id__in=ids_a_eliminar).delete() # Elimina los usuarios de la base de datos

    return JsonResponse({'success': True, 'deleted_count': delete_result}) # Retorna un JSON con el resultado de la eliminación de los usuarios


# =====================================================================
# VISTAS DE OBTENER USUARIO
# =====================================================================
@require_GET
def obtener_usuario_view(request, user_id): 
    """
    Vista AJAX para obtener un usuario (solo administradores). (ajax es una técnica que permite realizar peticiones a un servidor sin recargar la página.)
    
    Obtiene un usuario de la base de datos.
    
    Argumentos:
        request: Objeto HttpRequest de Django (solo GET permitido)
        user_id: ID del usuario a obtener
    """

    if 'user_id' not in request.session: # Si el usuario no está autenticado, retorna un error
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        admin_user = usuarios.objects.get(id=request.session['user_id']) # Obtiene el usuario autenticado   
        if not admin_user.rol:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403) # Si el usuario no es administrador, retorna un error
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Admin no válido'}, status=401) # Si el usuario no existe, retorna un error

    try:
        usuario = usuarios.objects.get(id=user_id) # Obtiene el usuario de la base de datos
        usuario_data = { # Diccionario de datos del usuario
            'id': str(usuario.id), # ID del usuario
            'nombre': usuario.nombre, # Nombre del usuario
            'correo': usuario.correo, # Correo del usuario
            'rol': usuario.rol, # Rol del usuario
            'foto_perfil': usuario.foto_perfil if usuario.foto_perfil else None # Foto de perfil del usuario
        }
        return JsonResponse({'success': True, 'usuario': usuario_data}) # Retorna un JSON con los datos del usuario
    except usuarios.DoesNotExist: # Si el usuario no existe, retorna un error
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404) # Si el usuario no existe, retorna un error
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error interno: {e}'}, status=500)


# =====================================================================
# VISTAS DE MODIFICAR USUARIO
# =====================================================================
@require_POST
def modificar_usuario_view(request):
    """
    Vista AJAX para modificar un usuario (solo administradores). (ajax es una técnica que permite realizar peticiones a un servidor sin recargar la página.)
    
    Modifica un usuario de la base de datos.
    """
    if 'user_id' not in request.session: # Si el usuario no está autenticado, retorna un error
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        admin_user = usuarios.objects.get(id=request.session['user_id']) 
        if not admin_user.rol:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403) # Si el usuario no es administrador, retorna un error
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Admin no válido'}, status=401) # Si el usuario no existe, retorna un error

    # Usar el formulario para validación
    form = UsuarioUpdateForm(request.POST, request.FILES) # Obtiene el formulario el post esta ahi para que el usuario ingrese los datos del formulario
    if not form.is_valid(): # Si el formulario no es válido, retorna un error
        # Retornar errores del formulario
        errors_dict = {} # Diccionario de errores del formulario
        for field, errors in form.errors.items():
            errors_dict[field] = errors # Asigna los errores del formulario al diccionario de errores
        return JsonResponse({'success': False, 'error': errors_dict}, status=400) # Retorna un JSON con los errores del formulario
    
    user_id = form.cleaned_data.get('user_id') # Obtiene el ID del usuario
    if not user_id: # Si el ID del usuario no existe, retorna un error
        return JsonResponse({'success': False, 'error': 'Falta user_id'}, status=400) # Si el ID del usuario no existe, retorna un error

    nombre = form.cleaned_data.get('nombre', '').strip() # Obtiene el nombre del usuario
    correo = form.cleaned_data.get('correo', '').strip() # Obtiene el correo del usuario
    contrasena = form.cleaned_data.get('contrasena', '') # Obtiene la contraseña del usuario
    rol = form.cleaned_data.get('rol', False) # Obtiene el rol del usuario

    if not nombre or not correo: # Si el nombre o el correo no existe, retorna un error
        return JsonResponse({'success': False, 'error': 'Nombre y correo son obligatorios.'}, status=400) # Si el nombre o el correo no existe, retorna un error

    try: 
        usuario_a_modificar = usuarios.objects.get(id=user_id) # Obtiene el usuario de la base de datos
        usuario_a_modificar.nombre = nombre
        usuario_a_modificar.correo = correo # Asigna el correo del usuario a la base de datos
        # Solo actualizar contraseña si se proporciona (y no está vacía)
        if contrasena and contrasena.strip(): # Si la contraseña no está vacía, hashea la contraseña
            # Hashear la nueva contraseña antes de guardar
            usuario_a_modificar.contrasena = _hash_password(contrasena)
        usuario_a_modificar.rol = rol # Asigna el rol del usuario a la base de datos
        
        # Manejar foto de perfil si se proporciona
        if 'foto_perfil' in request.FILES: # Si se proporciona una foto de perfil, se guarda la foto del usuario 
            try:
                # Eliminar foto anterior si existe
                if usuario_a_modificar.foto_perfil: # Si la foto de perfil existe, se elimina la foto de perfil
                    foto_antigua = settings.MEDIA_ROOT / usuario_a_modificar.foto_perfil # Obtiene la ruta de la foto de perfil
                    if foto_antigua.exists():
                        foto_antigua.unlink() # Elimina la foto de perfil
                
                foto_ruta = _guardar_foto_perfil(request.FILES['foto_perfil'], str(usuario_a_modificar.id)) # Guarda la foto del usuario
                usuario_a_modificar.foto_perfil = foto_ruta # Asigna la ruta de la foto al usuario esto se hace ya que estamos trabajando de forma local y no en la base de datos
            except ValueError as e: # Si hay error, retorna un error
                return JsonResponse({'success': False, 'error': str(e)}, status=400) # Si hay error, retorna un error
            except Exception as e: # Si hay error, retorna un error
                print(f"Error al guardar foto: {e}") # Imprime el error de guardado de la foto
                return JsonResponse({'success': False, 'error': f'Error al guardar foto: {e}'}, status=500) # Si hay error, retorna un error
        
        usuario_a_modificar.save() # Guarda el usuario en la base de datos
        _crear_log(admin_user, 'Modificar Usuario', usuario_afectado=usuario_a_modificar) # Crea el log de modificación de usuario
        return JsonResponse({'success': True})
    except usuarios.DoesNotExist: # Si el usuario no existe, retorna un error
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404) # Si el usuario no existe, retorna un error
    except Exception as e: # Si hay error, retorna un error
        print("Error interno modificar_usuario_view:", e) # Imprime el error de modificación de usuario
        return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'}, status=500) # Si hay error, retorna un error


# =====================================================================
# VISTAS DE LOGS Y AUDITORÍA
# =====================================================================

def ver_logs_view(request):
    """
    Vista para ver todos los logs del sistema (solo administradores).
    
    Muestra un registro completo de todas las acciones realizadas:
    - Crear, modificar, eliminar usuarios
    - Crear, modificar, eliminar calificaciones
    - Carga masiva de datos
    
    Argumentos:
        request: Objeto HttpRequest de Django
        
    Returns (lo que devuelve la funcion):
        HttpResponseForbidden: Si el usuario no es administrador
        HttpResponse: Renderiza ver_logs.html con la lista de logs
    """
    if 'user_id' not in request.session: # Si el usuario no está autenticado, redirige a login
        return redirect('login') 

    try:
        admin_user = usuarios.objects.get(id=request.session['user_id'])
        if not admin_user.rol:
            return HttpResponseForbidden( # Si el usuario no es administrador, retorna un error
                "<h1>Acceso Denegado</h1>"
                "<p>No tienes permisos de administrador.</p>"
                "<a href='/home/'>Volver</a>"
            )
    except usuarios.DoesNotExist: # Si el usuario no existe, redirige a login
        del request.session['user_id']
        del request.session['user_nombre']
        return redirect('login') # Si el usuario no existe, redirige a login

    try:
        logs_raw = Log.objects.no_dereference().order_by('-fecharegistrada') # Obtiene los logs de la base de datos
        logs_procesados = [] # Inicializa la lista de logs procesados

        for l in logs_raw: # Para cada log, se procesa el log
            # --- Actor (usuario que ejecutó la acción) ---
            actor_correo = getattr(l, "correoElectronico", "N/A") # Obtiene el correo del actor
            actor_id = "N/A" # Inicializa el ID del actor
            actor_nombre = "N/A" # Inicializa el nombre del actor
            
            if hasattr(l, "Usuarioid") and l.Usuarioid: # Si el log tiene un usuario, se obtiene el ID del usuario hasattr es una función que permite verificar si un objeto tiene un atributo
                actor_id_obj = _extraer_object_id(l.Usuarioid) # Extrae el ID del actor
                if actor_id_obj: # Si el ID del actor existe, se obtiene el ID del actor
                    actor_id = actor_id_obj # Asigna el ID del actor al actor
                    # Intentar obtener el nombre del actor si aún existe
                    try:
                        actor_usuario = usuarios.objects.get(id=actor_id_obj) # Obtiene el usuario de la base de datos
                        actor_nombre = actor_usuario.nombre # Asigna el nombre del actor al actor
                    except usuarios.DoesNotExist: # Si el usuario no existe, mantener N/A
                        pass  # El usuario ya no existe, mantener N/A

            # --- Usuario o elemento afectado (aunque haya sido eliminado) ---
            afectado_id = "N/A" # Inicializa el ID del afectado
            tipo_afectado = "N/A"  # 'Usuario' o 'Calificacion'
            
            if hasattr(l, "usuario_afectado") and l.usuario_afectado: # Si el log tiene un usuario afectado, se obtiene el ID del usuario afectado
                afectado_id_obj = _extraer_object_id(l.usuario_afectado) # Extrae el ID del usuario afectado
                if afectado_id_obj: # Si el ID del usuario afectado existe, se obtiene el ID del usuario afectado
                    afectado_id = afectado_id_obj # Asigna el ID del usuario afectado al afectado
                    tipo_afectado = "Usuario" # Asigna el tipo de afectado al usuario
            elif hasattr(l, "iddocumento") and l.iddocumento: # Si el log tiene un documento afectado, se obtiene el ID del documento afectado
                afectado_id_obj = _extraer_object_id(l.iddocumento) # Extrae el ID del documento afectado
                if afectado_id_obj: # Si el ID del documento afectado existe, se obtiene el ID del documento afectado
                    afectado_id = afectado_id_obj # Asigna el ID del documento afectado al afectado
                    tipo_afectado = "Calificacion" # Asigna el tipo de afectado a la calificación
            elif hasattr(l, "hash_archivo_csv") and l.hash_archivo_csv and getattr(l, "accion", "") == "Carga Masiva": # Si es una carga masiva, usar el hash del archivo como ID
                afectado_id = l.hash_archivo_csv # Usar el hash del archivo CSV como ID
                tipo_afectado = "Calificacion" # Las cargas masivas afectan calificaciones
            # Agregar el log procesado a la lista de logs procesados
            logs_procesados.append({
                "fecha": getattr(l, "fecharegistrada", None), # Asigna la fecha del log al log
                "actor_correo": actor_correo, # Asigna el correo del actor al log
                "actor_id": actor_id, # Asigna el ID del actor al log
                "actor_nombre": actor_nombre, # Asigna el nombre del actor al log
                "accion": getattr(l, "accion", "N/A"), # Asigna la acción al log
                "afectado_id": afectado_id, # Asigna el ID del afectado al log
                "tipo_afectado": tipo_afectado, # Asigna el tipo de afectado al log
            })

    except Exception as e: # Si hay error, retorna un error
        print(f"Error al cargar logs: {e}") # Imprime el error de carga de logs
        return HttpResponseServerError( # Si hay error, retorna un error
            f"<h1>Error Interno</h1>"
            f"<p>No se pudieron cargar los logs del sistema.</p>"
            f"<p>Error: {e}</p>"
            f"<a href='/home/'>Volver</a>"
        )

    context = {
        "user_nombre": admin_user.nombre, # Asigna el nombre del usuario al contexto
        "lista_logs": logs_procesados, # Asigna la lista de logs al contexto
    }
    return render(request, "prueba/ver_logs.html", context)


# =====================================================================
# VISTAS DE OBTENER CALIFICACIÓN
# =====================================================================
@require_GET
def obtener_calificacion_view(request, calificacion_id):
    """
    Vista AJAX para obtener una calificación por ID (solo administradores). (ajax es una técnica que permite realizar peticiones a un servidor sin recargar la página.)
    
    Obtiene una calificación de la base de datos.
    """
    if 'user_id' not in request.session: # Si el usuario no está autenticado, retorna un error
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        from decimal import Decimal # Importamos el modulo decimal para manejar números decimales
        calificacion = Calificacion.objects.get(id=calificacion_id) # Obtiene la calificación de la base de datos
        
        # Preparar datos para retornar
        calificacion_data = { # Diccionario de datos de la calificación
            'id': str(calificacion.id), # Asigna el ID de la calificación al diccionario de datos
            'mercado': calificacion.Mercado or '', # Asigna el mercado de la calificación al diccionario de datos
            'origen': calificacion.Origen or '', # Asigna el origen de la calificación al diccionario de datos
            'ejercicio': calificacion.Ejercicio or '', # Asigna el ejercicio de la calificación al diccionario de datos
            'instrumento': calificacion.Instrumento or '', # Asigna el instrumento de la calificación al diccionario de datos
            'descripcion': calificacion.Descripcion or '', # Asigna la descripción de la calificación al diccionario de datos
            'fecha_pago': calificacion.FechaPago.isoformat() if calificacion.FechaPago else '', # Asigna la fecha de pago de la calificación al diccionario de datos
            'secuencia_evento': calificacion.SecuenciaEvento or '', # Asigna la secuencia de evento de la calificación al diccionario de datos
            'dividendo': str(calificacion.Dividendo or 0.0), # Asigna el dividendo de la calificación al diccionario de datos
            'isfut': calificacion.ISFUT or False, # Asigna el ISFUT de la calificación al diccionario de datos
            'anho': calificacion.Anho or calificacion.Ejercicio or '', # Asigna el año de la calificación al diccionario de datos
            'valor_historico': str(calificacion.ValorHistorico or 0.0), # Asigna el valor histórico de la calificación al diccionario de datos
            'factor_actualizacion': str(calificacion.FactorActualizacion or 0.0), # Asigna el factor de actualización de la calificación al diccionario de datos
            'montos': {}, # Asigna los montos de la calificación al diccionario de datos
            'factores': {} # Asigna los factores de la calificación al diccionario de datos
        }
        
        # Obtener la suma base guardada
        suma_base = calificacion.SumaBase or Decimal(0) # Obtiene la suma base de la calificación
        
        # Calcular los montos a partir de los factores guardados (cálculo inverso)
        # monto = factor * suma_base
        for i in range(8, 38): # range(8, 38) se refiere a que se agregan los factores F8 a F37
            factor_field = f'Factor{i:02d}'
            factor_value = getattr(calificacion, factor_field, Decimal(0)) # getattr se refiere a que se obtiene el valor del campo factor_field de la calificación
            if suma_base > 0: # Si la suma base es mayor a 0, se calcula el monto
                monto_calculado = (factor_value * suma_base).quantize(Decimal('0.01')) # Se calcula el monto
            else: # Si la suma base es menor o igual a 0, se asigna 0 al monto
                monto_calculado = Decimal(0) # Se asigna 0 al monto
            
            monto_field = f'Monto{i:02d}' # Se asigna el nombre del campo monto al campo monto_field
            calificacion_data['montos'][monto_field] = str(monto_calculado) if monto_calculado else '0.0' # Se asigna el monto al diccionario de datos
            
            # También incluir los factores para referencia
            calificacion_data['factores'][factor_field] = str(factor_value) if factor_value else '0.0' # Se asigna el factor al diccionario de datos
        
        return JsonResponse({ # Se retorna un JSON con los datos de la calificación
            'success': True,
            'calificacion': calificacion_data
        }) # Se retorna un JSON con los datos de la calificación
    except Calificacion.DoesNotExist: # Si la calificación no existe, retorna un error
        return JsonResponse({'success': False, 'error': 'Calificación no encontrada'}, status=404) # Si la calificación no existe, retorna un error
    except Exception as e: # Si hay error, retorna un error
        return JsonResponse({'success': False, 'error': f'Error al obtener calificación: {str(e)}'}, status=500) # Si hay error, retorna un error


# =====================================================================
# VISTAS DE ELIMINAR CALIFICACIÓN
# =====================================================================
@require_POST
def eliminar_calificacion_view(request, calificacion_id):
    """Vista para eliminar una calificación (solo administradores). (ajax es una técnica que permite realizar peticiones a un servidor sin recargar la página.)
    
    Elimina una calificación de la base de datos.
    """
    if 'user_id' not in request.session: # Si el usuario no está autenticado, retorna un error
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        current_user = usuarios.objects.get(id=request.session['user_id']) # Obtiene el usuario autenticado
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401) # Si el usuario no existe, retorna un error

    try:
        calificacion = Calificacion.objects.get(id=calificacion_id) # Obtiene la calificación de la base de datos
        
        # Si la calificación proviene de un CSV, verificar si quedan más calificaciones de ese archivo
        hash_archivo_csv = None
        if calificacion.Origen == 'csv' and hasattr(calificacion, 'hash_archivo_csv') and calificacion.hash_archivo_csv:
            hash_archivo_csv = calificacion.hash_archivo_csv
        
        calificacion.delete() # Elimina la calificación de la base de datos
        
        # Si la calificación venía de un CSV, verificar si quedan más calificaciones de ese archivo
        if hash_archivo_csv:
            from .models import ArchivoCSV
            # Verificar si quedan calificaciones con ese hash
            calificaciones_restantes = Calificacion.objects(
                Origen='csv',
                hash_archivo_csv=hash_archivo_csv
            ).count()
            
            # Si no quedan calificaciones de ese archivo, eliminar el registro de ArchivoCSV
            # para permitir subirlo nuevamente
            if calificaciones_restantes == 0:
                archivo_csv = ArchivoCSV.objects(hash_archivo=hash_archivo_csv).first()
                if archivo_csv:
                    archivo_csv.delete()
                    print(f"[ELIMINAR] Se eliminó el registro de ArchivoCSV (hash: {hash_archivo_csv}) porque no quedan calificaciones")
        
        _crear_log(current_user, 'Eliminar Calificacion', documento_afectado=calificacion) # Crea el log de eliminación de calificación             
        return JsonResponse({'success': True, 'message': 'Calificación eliminada exitosamente'}) # Se retorna un JSON con el mensaje de eliminación de calificación
    except Calificacion.DoesNotExist: # Si la calificación no existe, retorna un error
        return JsonResponse({'success': False, 'error': 'Calificación no encontrada'}, status=404) # Si la calificación no existe, retorna un error
    except Exception as e: # Si hay error, retorna un error
        return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'}, status=500) # Si hay error, retorna un error

# =====================================================================
# VISTAS DE COPIAR CALIFICACIÓN
# =====================================================================

@require_POST
def copiar_calificacion_view(request, calificacion_id):
    """Vista para copiar una calificación completa con un nuevo ID (solo administradores). (ajax es una técnica que permite realizar peticiones a un servidor sin recargar la página.)
    
    Copia una calificación de la base de datos.
    """
    print(f"[COPiar] Iniciando copia de calificación ID: {calificacion_id}")
    
    if 'user_id' not in request.session: # Si el usuario no está autenticado, retorna un error  
        print("[COPiar] Error: No autenticado")
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        current_user = usuarios.objects.get(id=request.session['user_id']) # Obtiene el usuario autenticado
        print(f"[COPiar] Usuario autenticado: {current_user.correo}") # Imprime el correo del usuario autenticado
    except usuarios.DoesNotExist: # Si el usuario no existe, retorna un error
        print("[COPiar] Error: Usuario no válido") # Imprime el error de usuario no válido
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401) # Si el usuario no existe, retorna un error

    try:
        from decimal import Decimal # Importamos el modulo decimal para manejar números decimales
        
        # Obtener la calificación original
        print(f"[COPiar] Obteniendo calificación original: {calificacion_id}") # Imprime el ID de la calificación original
        calificacion_original = Calificacion.objects.get(id=calificacion_id) # Obtiene la calificación original de la base de datos get es una función que permite obtener un documento de la base de datos
        print(f"[COPiar] Calificación encontrada: {calificacion_original.Instrumento}") # Imprime el instrumento de la calificación original
        
        # Crear una nueva calificación copiando todos los campos
        nueva_calificacion = Calificacion() # Crea una nueva calificación
        
        # Copiar campos básicos
        nueva_calificacion.Mercado = calificacion_original.Mercado # Copia el mercado de la calificación original a la nueva calificación
        nueva_calificacion.Origen = calificacion_original.Origen # Copia el origen de la calificación original a la nueva calificación
        nueva_calificacion.Ejercicio = calificacion_original.Ejercicio # Copia el ejercicio de la calificación original a la nueva calificación
        nueva_calificacion.Instrumento = calificacion_original.Instrumento # Copia el instrumento de la calificación original a la nueva calificación
        nueva_calificacion.EventoCapital = calificacion_original.EventoCapital # Copia el evento capital de la calificación original a la nueva calificación
        nueva_calificacion.FechaPago = calificacion_original.FechaPago # Copia la fecha de pago de la calificación original a la nueva calificación
        nueva_calificacion.SecuenciaEvento = calificacion_original.SecuenciaEvento # Copia la secuencia de evento de la calificación original a la nueva calificación
        nueva_calificacion.Descripcion = calificacion_original.Descripcion # Copia la descripción de la calificación original a la nueva calificación
        nueva_calificacion.Dividendo = calificacion_original.Dividendo # Copia el dividendo de la calificación original a la nueva calificación
        nueva_calificacion.ISFUT = calificacion_original.ISFUT # Copia el ISFUT de la calificación original a la nueva calificación
        nueva_calificacion.ValorHistorico = calificacion_original.ValorHistorico # Copia el valor histórico de la calificación original a la nueva calificación
        nueva_calificacion.FactorActualizacion = calificacion_original.FactorActualizacion # Copia el factor de actualización de la calificación original a la nueva calificación
        nueva_calificacion.Anho = calificacion_original.Anho # Copia el año de la calificación original a la nueva calificación
        nueva_calificacion.RentasExentas = calificacion_original.RentasExentas # Copia las rentas exentas de la calificación original a la nueva calificación
        nueva_calificacion.Factor19A = calificacion_original.Factor19A # Copia el factor 19A de la calificación original a la nueva calificación
        
        # Copiar todos los factores (Factor08 a Factor37) esto para que se copien los factores de la calificación original a la nueva calificación
        print("[COPiar] Copiando factores...") # Imprime el mensaje de copia de factores
        for i in range(8, 38): # range(8, 38) se refiere a que se copian los factores F8 a F37
            factor_field = f'Factor{i:02d}' # Se asigna el nombre del campo factor al campo factor_field
            valor_factor = getattr(calificacion_original, factor_field, Decimal(0)) # getattr se refiere a que se obtiene el valor del campo factor_field de la calificación
            setattr(nueva_calificacion, factor_field, valor_factor) # setattr se refiere a que se asigna el valor del campo factor_field de la calificación a la nueva calificación
        
        # Copiar todos los montos (Monto08 a Monto37) esto para que se copien los montos de la calificación original a la nueva calificación
        print("[COPiar] Copiando montos...") # Imprime el mensaje de copia de montos
        for i in range(8, 38):
            monto_field = f'Monto{i:02d}' # Se asigna el nombre del campo monto al campo monto_field
            valor_monto = getattr(calificacion_original, monto_field, Decimal(0)) # getattr se refiere a que se obtiene el valor del campo monto_field de la calificación
            setattr(nueva_calificacion, monto_field, valor_monto) # setattr se refiere a que se asigna el valor del campo monto_field de la calificación a la nueva calificación
        
        # Copiar SumaBase
        nueva_calificacion.SumaBase = calificacion_original.SumaBase # Copia la suma base de la calificación original a la nueva calificación
        
        # FechaAct se establecerá automáticamente al guardar (default=datetime.datetime.now)
        nueva_calificacion.FechaAct = datetime.datetime.now() # Asigna la fecha de actualización de la calificación a la nueva calificación
        
        # Guardar la nueva calificación
        print("[COPiar] Guardando nueva calificación...") # Imprime el mensaje de guardado de la nueva calificación
        nueva_calificacion.save()
        print(f"[COPiar] Nueva calificación guardada con ID: {nueva_calificacion.id}") # Imprime el ID de la nueva calificación
        
        # Crear log de la acción
        try:
            _crear_log(current_user, 'Crear Calificacion', documento_afectado=nueva_calificacion)
            print("[COPiar] Log creado exitosamente") # Imprime el mensaje de creación de log
        except Exception as log_error:
            print(f"[COPiar] Advertencia: Error al crear log: {log_error}") # Imprime el error de creación de log
        
        return JsonResponse({ # Se retorna un JSON con el mensaje de copia de calificación
            'success': True,
            'message': 'Calificación copiada exitosamente', # Asigna el mensaje de copia de calificación al JSON
            'nueva_calificacion_id': str(nueva_calificacion.id) # Asigna el ID de la nueva calificación al JSON
        }) # Se retorna un JSON con el mensaje de copia de calificación
        
    except Calificacion.DoesNotExist: 
        print(f"[COPiar] Error: Calificación no encontrada: {calificacion_id}")
        return JsonResponse({'success': False, 'error': 'Calificación no encontrada'}, status=404) # Se retorna un JSON con el error de no encontrada de la calificación
    except Exception as e:
        import traceback
        print(f"[COPiar] Error al copiar calificación: {e}") # Imprime el error de copia de calificación
        print(f"[COPiar] Traceback: {traceback.format_exc()}") # Imprime el traceback de la excepción
        return JsonResponse({'success': False, 'error': f'Error al copiar: {str(e)}'}, status=500) # Se retorna un JSON con el error de copia de calificación


# =====================================================================
# VISTAS DE CARGA MASIVA (CSV)
# =====================================================================

@require_POST
def preview_factor_view(request):
    """
    Vista AJAX para previsualizar archivo CSV con factores.
    
    Lee un archivo CSV que contiene factores ya calculados.
    Valida el formato y retorna los datos para mostrarlos en una tabla de previsualización.
    Calcula un hash único del contenido para evitar duplicados.
    
    Argumentos:
        request: Objeto HttpRequest de Django (solo POST permitido)
        
    Returns (lo que devuelve la funcion):
        JsonResponse: JSON con datos del CSV para previsualizar, incluyendo hash del archivo
    """
    if 'user_id' not in request.session: # Si el usuario no está autenticado, retorna un error
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        current_user = usuarios.objects.get(id=request.session['user_id']) # Obtiene el usuario autenticado
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401)

    try: 
        import pandas as pd # Importamos el modulo pandas para manejar datos en tablas
        from decimal import Decimal # Importamos el modulo decimal para manejar números decimales
        import hashlib # Importamos hashlib para calcular hash del archivo
        
        if 'archivo' not in request.FILES: # Si no se recibió ningún archivo, retorna un error
            return JsonResponse({'success': False, 'error': 'No se recibió ningún archivo'}, status=400) # Se retorna un JSON con el error de no recibido de archivo
        
        archivo = request.FILES['archivo'] # Obtiene el archivo de la solicitud
        
        # Calcular hash del contenido del archivo para identificar duplicados
        archivo.seek(0)  # Asegurar que estamos al inicio del archivo
        contenido = archivo.read()
        hash_archivo = hashlib.sha256(contenido).hexdigest()  # Calcular hash SHA-256
        archivo.seek(0)  # Volver al inicio para leer el CSV
        
        # Verificar si este archivo ya fue subido anteriormente
        from .models import ArchivoCSV
        archivo_existente = ArchivoCSV.objects(hash_archivo=hash_archivo).first()
        if archivo_existente:
            # Verificar si todavía existen calificaciones con este hash de archivo CSV
            # Buscar calificaciones que tengan el hash_archivo_csv específico
            calificaciones_existentes = Calificacion.objects(
                Origen='csv',
                hash_archivo_csv=hash_archivo
            ).count()
            
            print(f"[PREVIEW_FACTOR] Archivo duplicado encontrado. Calificaciones existentes con hash {hash_archivo}: {calificaciones_existentes}")
            
            # Si no hay calificaciones con ese hash, eliminar el registro de ArchivoCSV para permitir subirlo nuevamente
            if calificaciones_existentes == 0:
                archivo_existente.delete()
                print(f"[PREVIEW_FACTOR] Se eliminó el registro de ArchivoCSV porque no quedan calificaciones. Permitiendo subida.")
            else:
                # Si hay calificaciones, mostrar error de duplicado
                return JsonResponse({
                    'success': False, 
                    'error': f'Este archivo ya fue subido anteriormente el {archivo_existente.fecha_subida.strftime("%Y-%m-%d %H:%M:%S")} por {archivo_existente.usuario.correo} y todavía existen {calificaciones_existentes} calificación(es) creadas desde ese archivo.',
                    'duplicado': True,
                    'hash_archivo': hash_archivo
                }, status=400)
        
        # Leer CSV con pandas
        try:
            # Intentar diferentes encodings (encodings se refiere a los caracteres que se usan en el archivo)
            try:
                df = pd.read_csv(archivo, encoding='utf-8')
            except UnicodeDecodeError: # Si hay error de decodificación de caracteres, retorna un error
                archivo.seek(0)
                df = pd.read_csv(archivo, encoding='latin-1') # Si hay error de decodificación de caracteres, retorna un error
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al leer el archivo CSV: {str(e)}'}, status=400) # Se retorna un JSON con el error de lectura de archivo
        
        # Limpiar nombres de columnas (eliminar espacios)
        df.columns = df.columns.str.strip() # Se eliminan los espacios de los nombres de las columnas
        
        # Eliminar filas completamente vacías
        df = df.dropna(how='all') # Se eliminan las filas completamente vacías
        
        # Convertir a lista de diccionarios
        datos = [] # Se crea una lista para los datos
        errores = [] # Se crea una lista para los errores
        
        for idx, row in df.iterrows(): # Se recorre el dataframe
            try:
                # Convertir la fila a diccionario
                fila = row.to_dict() # Se convierte la fila a un diccionario
                
                # Convertir valores NaN a strings vacíos y limpiar
                fila_limpia = {} # Se crea un diccionario para la fila limpia
                for key, value in fila.items():
                    if pd.isna(value):
                        fila_limpia[key] = '' # Se asigna un string vacío al diccionario de la fila limpia
                    else:
                        fila_limpia[key] = str(value).strip() if value else '' # Se asigna el valor de la fila limpia al diccionario de la fila limpia
                
                # Validar campos requeridos (buscar con diferentes variaciones)
                ejercicio = fila_limpia.get('Ejercicio') or fila_limpia.get('ejercicio') or '' # Se obtiene el valor del campo Ejercicio de la fila limpia
                mercado = fila_limpia.get('Mercado') or fila_limpia.get('mercado') or '' # Se obtiene el valor del campo Mercado de la fila limpia
                
                if not ejercicio or not mercado:
                    errores.append(f'Fila {idx + 2}: Faltan campos requeridos (Ejercicio, Mercado)') # Se agrega el error a la lista de errores
                    continue
                
                datos.append(fila_limpia) # Se agrega la fila limpia a la lista de datos
                
            except Exception as e:
                errores.append(f'Fila {idx + 2}: {str(e)}') # Se agrega el error a la lista de errores
                continue
        
        return JsonResponse({ # Se retorna un JSON con los datos de la previsualización
            'success': True,
            'datos': datos, # Se asigna la lista de datos al JSON
            'errores': errores, # Se asigna la lista de errores al JSON
            'total': len(datos), # Se asigna el total de datos al JSON
            'hash_archivo': hash_archivo, # Hash único del archivo para evitar duplicados
            'nombre_archivo': archivo.name  # Nombre original del archivo
        }) # Se retorna un JSON con los datos de la previsualización
        
    except Exception as e:
        print(f"Error al previsualizar factor: {e}") # Imprime el error de previsualización de factor
        import traceback
        print(traceback.format_exc()) # Imprime el traceback de la excepción
        return JsonResponse({'success': False, 'error': f'Error al procesar: {str(e)}'}, status=500) # Se retorna un JSON con el error de procesamiento


# =====================================================================
# VISTAS DE PREVISUALIZACIÓN DE MONTOS
# =====================================================================
@require_POST
def preview_monto_view(request):
    """Vista para previsualizar archivo CSV con montos (ajax es una técnica que permite realizar peticiones a un servidor sin recargar la página.)
    
    Previsualiza un archivo CSV que contiene montos ya calculados.
    """
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401) # Se retorna un JSON con el error de no autenticado

    try:
        current_user = usuarios.objects.get(id=request.session['user_id']) # Obtiene el usuario autenticado
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401) # Se retorna un JSON con el error de usuario no válido

    try:
        import pandas as pd # Importamos el modulo pandas para manejar datos en tablas  
        from decimal import Decimal # Importamos el modulo decimal para manejar números decimales
        import hashlib # Importamos hashlib para calcular hash del archivo
        
        if 'archivo' not in request.FILES: # Si no se recibió ningún archivo, retorna un error
            return JsonResponse({'success': False, 'error': 'No se recibió ningún archivo'}, status=400)
        
        archivo = request.FILES['archivo'] # Obtiene el archivo de la solicitud
        
        # Calcular hash del contenido del archivo para identificar duplicados
        archivo.seek(0)  # Asegurar que estamos al inicio del archivo
        contenido = archivo.read()
        hash_archivo = hashlib.sha256(contenido).hexdigest()  # Calcular hash SHA-256
        archivo.seek(0)  # Volver al inicio para leer el CSV
        
        # Verificar si este archivo ya fue subido anteriormente
        from .models import ArchivoCSV
        archivo_existente = ArchivoCSV.objects(hash_archivo=hash_archivo).first()
        if archivo_existente:
            # Verificar si todavía existen calificaciones con este hash de archivo CSV
            calificaciones_existentes = Calificacion.objects(
                Origen='csv',
                hash_archivo_csv=hash_archivo
            ).count()
            
            print(f"[PREVIEW_MONTO] Archivo duplicado encontrado. Calificaciones existentes con hash {hash_archivo}: {calificaciones_existentes}")
            
            # Si no hay calificaciones con ese hash, eliminar el registro de ArchivoCSV para permitir subirlo nuevamente
            if calificaciones_existentes == 0:
                archivo_existente.delete()
                print(f"[PREVIEW_MONTO] Se eliminó el registro de ArchivoCSV porque no quedan calificaciones. Permitiendo subida.")
            else:
                # Si hay calificaciones, mostrar error de duplicado
                return JsonResponse({
                    'success': False, 
                    'error': f'Este archivo ya fue subido anteriormente el {archivo_existente.fecha_subida.strftime("%Y-%m-%d %H:%M:%S")} por {archivo_existente.usuario.correo} y todavía existen {calificaciones_existentes} calificación(es) creadas desde ese archivo.',
                    'duplicado': True,
                    'hash_archivo': hash_archivo
                }, status=400)
        
        # Leer CSV con pandas
        try:
            # Intentar diferentes encodings (encodings se refiere a los caracteres que se usan en el archivo)
            try:
                df = pd.read_csv(archivo, encoding='utf-8')
            except UnicodeDecodeError: # Si hay error de decodificación de caracteres, retorna un error
                archivo.seek(0)
                df = pd.read_csv(archivo, encoding='latin-1') # Si hay error de decodificación de caracteres, retorna un error
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al leer el archivo CSV: {str(e)}'}, status=400) # Se retorna un JSON con el error de lectura de archivo
        
        # Limpiar nombres de columnas (eliminar espacios)
        df.columns = df.columns.str.strip() # Se eliminan los espacios de los nombres de las columnas
        
        # Eliminar filas completamente vacías
        df = df.dropna(how='all') # Se eliminan las filas completamente vacías
        
        # Convertir a lista de diccionarios
        datos = [] # Se crea una lista para los datos
        errores = [] # Se crea una lista para los errores
        
        for idx, row in df.iterrows(): # Se recorre el dataframe
            try:
                # Convertir la fila a diccionario
                fila = row.to_dict() # Se convierte la fila a un diccionario
                
                # Convertir valores NaN a strings vacíos y limpiar
                fila_limpia = {} # Se crea un diccionario para la fila limpia
                for key, value in fila.items():
                    if pd.isna(value):
                        fila_limpia[key] = '' # Se asigna un string vacío al diccionario de la fila limpia
                    else:
                        fila_limpia[key] = str(value).strip() if value else '' # Se asigna el valor de la fila limpia al diccionario de la fila limpia
                
                # Validar campos requeridos (buscar con diferentes variaciones)
                ejercicio = fila_limpia.get('Ejercicio') or fila_limpia.get('ejercicio') or '' # Se obtiene el valor del campo Ejercicio de la fila limpia
                mercado = fila_limpia.get('Mercado') or fila_limpia.get('mercado') or '' # Se obtiene el valor del campo Mercado de la fila limpia
                
                if not ejercicio or not mercado:
                    errores.append(f'Fila {idx + 2}: Faltan campos requeridos (Ejercicio, Mercado)') # Se agrega el error a la lista de errores
                    continue
                
                datos.append(fila_limpia) # Se agrega la fila limpia a la lista de datos
                
            except Exception as e:
                errores.append(f'Fila {idx + 2}: {str(e)}') # Se agrega el error a la lista de errores
                continue
        
        return JsonResponse({ # Se retorna un JSON con los datos de la previsualización
            'success': True,
            'datos': datos, # Se asigna la lista de datos al JSON
            'errores': errores, # Se asigna la lista de errores al JSON
            'total': len(datos), # Se asigna el total de datos al JSON
            'hash_archivo': hash_archivo, # Hash único del archivo para evitar duplicados
            'nombre_archivo': archivo.name  # Nombre original del archivo
        }) # Se retorna un JSON con los datos de la previsualización
        
    except Exception as e:
        print(f"Error al previsualizar monto: {e}") # Imprime el error de previsualización de monto
        import traceback
        print(traceback.format_exc()) # Imprime el traceback de la excepción
        return JsonResponse({'success': False, 'error': f'Error al procesar: {str(e)}'}, status=500) # Se retorna un JSON con el error de procesamiento


# =====================================================================
# VISTAS DE CARGA MASIVA DE FACTORES
# =====================================================================
@require_POST
def cargar_factor_view(request):
    """
    Vista AJAX para cargar calificaciones desde CSV con factores ya calculados.
    
    Procesa un CSV que contiene factores financieros ya calculados.
    Crea múltiples calificaciones en la base de datos en una sola operación.
    
    Flujo:
    1. Recibe datos del CSV (después de previsualización)
    2. Valida cada fila
    3. Crea calificaciones en MongoDB
    4. Crea log de carga masiva
    
    Argumentos:
        request: Objeto HttpRequest de Django (solo POST permitido)
        
    Returns (lo que devuelve la funcion):
        JsonResponse: JSON con cantidad de calificaciones creadas y errores encontrados
    """
    print("[CARGAR_FACTOR] Iniciando carga de factores...") # Imprime el mensaje de inicio de carga de factores
    
    if 'user_id' not in request.session: # Si el usuario no está autenticado, retorna un error
        print("[CARGAR_FACTOR] Error: No autenticado")
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401) # Se retorna un JSON con el error de no autenticado

    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
        print(f"[CARGAR_FACTOR] Usuario autenticado: {current_user.correo}")
    except usuarios.DoesNotExist:
        print("[CARGAR_FACTOR] Error: Usuario no válido") # Imprime el error de usuario no válido
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401) # Se retorna un JSON con el error de usuario no válido

    try:
        import pandas as pd # Importamos el modulo pandas para manejar datos en tablas
        import json # Importamos el modulo json para manejar datos en formato JSON 
        from decimal import Decimal # Importamos el modulo decimal para manejar números decimales
        
        print("[CARGAR_FACTOR] Parseando JSON...") # Imprime el mensaje de parseo de JSON
        data = json.loads(request.body) # Se carga el JSON de la solicitud
        datos_csv = data.get('datos', []) # Se obtiene los datos del JSON
        hash_archivo = data.get('hash_archivo', '') # Se obtiene el hash del archivo
        nombre_archivo = data.get('nombre_archivo', 'archivo.csv') # Se obtiene el nombre del archivo
        
        print(f"[CARGAR_FACTOR] Datos recibidos: {len(datos_csv)} filas") # Imprime el mensaje de datos recibidos
        print(f"[CARGAR_FACTOR] Hash del archivo: {hash_archivo}") # Imprime el hash del archivo
        
        if not datos_csv:
            print("[CARGAR_FACTOR] Error: No se recibieron datos") # Imprime el error de no recibido de datos
            return JsonResponse({'success': False, 'error': 'No se recibieron datos'}, status=400) # Se retorna un JSON con el error de no recibido de datos
        
        # Verificar si este archivo ya fue procesado (doble verificación)
        if hash_archivo:
            from .models import ArchivoCSV
            archivo_existente = ArchivoCSV.objects(hash_archivo=hash_archivo).first()
            if archivo_existente:
                # Verificar si todavía existen calificaciones con este hash de archivo CSV
                calificaciones_existentes = Calificacion.objects(
                    Origen='csv',
                    hash_archivo_csv=hash_archivo
                ).count()
                
                print(f"[CARGAR_FACTOR] Archivo duplicado encontrado. Calificaciones existentes con hash {hash_archivo}: {calificaciones_existentes}")
                
                # Si no hay calificaciones con ese hash, eliminar el registro de ArchivoCSV para permitir subirlo nuevamente
                if calificaciones_existentes == 0:
                    archivo_existente.delete()
                    print(f"[CARGAR_FACTOR] Se eliminó el registro de ArchivoCSV porque no quedan calificaciones. Permitiendo subida.")
                else:
                    print(f"[CARGAR_FACTOR] Error: Archivo duplicado detectado. Hash: {hash_archivo}")
                    return JsonResponse({
                        'success': False, 
                        'error': f'Este archivo ya fue procesado anteriormente el {archivo_existente.fecha_subida.strftime("%Y-%m-%d %H:%M:%S")} por {archivo_existente.usuario.correo} y todavía existen {calificaciones_existentes} calificación(es) creadas desde ese archivo.',
                        'duplicado': True
                    }, status=400)
        
        # Convertir a DataFrame de pandas para procesamiento más eficiente
        df = pd.DataFrame(datos_csv) # Se convierte el JSON a un dataframe de pandas
        
        # Limpiar nombres de columnas (eliminar espacios)
        df.columns = df.columns.str.strip() # Se eliminan los espacios de los nombres de las columnas
        
        # Eliminar filas completamente vacías
        df = df.dropna(how='all') # Se eliminan las filas completamente vacías
        
        calificaciones_creadas = 0 # Se inicializa la variable de calificaciones creadas
        errores = [] # Se inicializa la variable de errores
        
        # Iterar sobre el DataFrame
        for idx, row in df.iterrows():
            fila_num = idx + 2  # +2 porque idx empieza en 0 y la fila 1 es el encabezado
            try:
                # Convertir la fila a diccionario
                fila = row.to_dict()
                
                # Convertir valores NaN a strings vacíos y limpiar
                fila_limpia = {} # Se crea un diccionario para la fila limpia
                for key, value in fila.items():
                    if pd.isna(value):
                        fila_limpia[key] = ''
                    else:
                        fila_limpia[key] = str(value).strip() if value else '' # Se asigna el valor de la fila limpia al diccionario de la fila limpia
                
                # Debug: mostrar las claves disponibles en la primera fila
                if fila_num == 2:
                    print(f"[CARGAR_FACTOR] Claves disponibles en CSV: {list(fila_limpia.keys())}")
                    print(f"[CARGAR_FACTOR] Primera fila completa: {fila_limpia}")
                    print(f"[CARGAR_FACTOR] Ejercicio raw: '{fila_limpia.get('Ejercicio')}'")
                    print(f"[CARGAR_FACTOR] Mercado raw: '{fila_limpia.get('Mercado')}'")
                    print(f"[CARGAR_FACTOR] Instrumento raw: '{fila_limpia.get('Instrumento')}'")
                
                # Validar campos requeridos (buscar con diferentes variaciones)
                # Primero intentar obtener Ejercicio
                ejercicio = fila_limpia.get('Ejercicio') or fila_limpia.get('ejercicio') or ''
                mercado_raw = fila_limpia.get('Mercado') or fila_limpia.get('mercado') or ''
                instrumento = fila_limpia.get('Instrumento') or fila_limpia.get('instrumento') or ''
                
                # Normalizar mercado a los valores válidos (acciones, CFI, Fondos mutuos)
                mercado_normalizado = mercado_raw
                if mercado_raw: # Si el mercado no es None, normaliza el mercado
                    mercado_lower = mercado_raw.lower().strip() # Se convierte el mercado a minúsculas y se eliminan los espacios
                    if mercado_lower == 'acciones' or mercado_lower == 'accion':
                        mercado_normalizado = 'acciones' # Se asigna el valor de acciones al mercado normalizado
                    elif mercado_lower == 'cfi':
                        mercado_normalizado = 'CFI' # Se asigna el valor de CFI al mercado normalizado
                    elif mercado_lower == 'fondos mutuos' or mercado_lower == 'fondosmutuos' or mercado_lower == 'fondo mutuo':
                        mercado_normalizado = 'Fondos mutuos' # Se asigna el valor de Fondos mutuos al mercado normalizado
                
                mercado = mercado_normalizado # Se asigna el valor del mercado normalizado al mercado
                
                # Detectar si Ejercicio e Instrumento están intercambiados
                # Si Ejercicio contiene letras (como "ACC001") e Instrumento es numérico, intercambiar
                ejercicio_es_numero = False # Se inicializa la variable de ejercicio es numero
                instrumento_es_numero = False # Se inicializa la variable de instrumento es numero
                ejercicio_tiene_letras = any(c.isalpha() for c in str(ejercicio)) if ejercicio else False # Se inicializa la variable de ejercicio tiene letras
                
                try:
                    int(ejercicio) # Se convierte el ejercicio a entero
                    ejercicio_es_numero = True # Se asigna el valor de True a la variable de ejercicio es numero
                except (ValueError, TypeError):
                    pass # Si hay error, se pasa al siguiente try
                
                try:
                    int(instrumento) # Se convierte el instrumento a entero
                    instrumento_es_numero = True # Se asigna el valor de True a la variable de instrumento es numero
                except (ValueError, TypeError):
                    pass # Si hay error, se pasa al siguiente try
                
                # Si Ejercicio no es numérico pero Instrumento sí, intercambiar
                # O si Ejercicio tiene letras (código de instrumento) e Instrumento es numérico (año)
                if (not ejercicio_es_numero and instrumento_es_numero) or (ejercicio_tiene_letras and instrumento_es_numero): # Si Ejercicio no es numérico pero Instrumento sí, intercambiar o si Ejercicio tiene letras (código de instrumento) e Instrumento es numérico (año)
                    print(f"[CARGAR_FACTOR] Advertencia: Ejercicio e Instrumento parecen estar intercambiados en fila {idx}. Ejercicio: '{ejercicio}', Instrumento: '{instrumento}'")
                    ejercicio, instrumento = instrumento, ejercicio
                    ejercicio_es_numero = True # Se asigna el valor de True a la variable de ejercicio es numero
                
                if not ejercicio or not mercado: # Si Ejercicio o Mercado no es None, mostrar qué claves tiene la fila para ayudar a debuggear
                    # Mostrar qué claves tiene la fila para ayudar a debuggear
                    claves_disponibles = ', '.join(fila.keys()) # Se obtiene las claves de la fila
                    errores.append(f'Fila {idx}: Faltan campos requeridos (Ejercicio, Mercado). Claves disponibles: {claves_disponibles}') # Se agrega el error a la lista de errores
                    continue # Se pasa al siguiente try
                
                # Validar y convertir Ejercicio a entero (si no es un número entero, mostrar el error)
                try:
                    ejercicio_int = int(ejercicio) # Se convierte el ejercicio a entero
                except (ValueError, TypeError): # Si hay error, se pasa al siguiente try
                    # Mostrar más información sobre el error
                    claves_disponibles = ', '.join(fila.keys()) # Se obtiene las claves de la fila
                    errores.append(f'Fila {idx}: El campo Ejercicio debe ser un número entero. Valor recibido: "{ejercicio}". Instrumento recibido: "{instrumento}". Claves disponibles: {claves_disponibles}') # Se agrega el error a la lista de errores
                    continue # Se pasa al siguiente try
                
                # Crear nueva calificación (se crea un nuevo documento en la base de datos) para la calificación
                nueva_calificacion = Calificacion()
                nueva_calificacion.Ejercicio = ejercicio_int # Se asigna el valor del ejercicio a la nueva calificación
                nueva_calificacion.Mercado = mercado # Se asigna el valor del mercado a la nueva calificación
                nueva_calificacion.Instrumento = instrumento # Se asigna el valor del instrumento a la nueva calificación
                nueva_calificacion.Origen = 'csv'  # Normalizado a minúsculas para coincidir con el filtro
                nueva_calificacion.hash_archivo_csv = hash_archivo  # Guardar el hash del archivo CSV para relacionar la calificación con el archivo
                nueva_calificacion.Descripcion = fila_limpia.get('DESCRIPCION') or fila_limpia.get('Descripcion') or fila_limpia.get('descripcion') or '' # Se asigna el valor de la descripción a la nueva calificación
                
                # Fecha de pago usando pandas (se convierte la fecha de pago a un objeto datetime)
                fecha_pago = fila_limpia.get('FEC_PAGO') or fila_limpia.get('Fec_Pago') or fila_limpia.get('fec_pago') or '' # Se obtiene el valor de la fecha de pago
                if fecha_pago: # Si la fecha de pago no es None, se convierte a datetime
                    try:
                        fecha_parsed = pd.to_datetime(fecha_pago, format='%Y-%m-%d', errors='coerce') # Se convierte la fecha de pago a un objeto datetime
                        if not pd.isna(fecha_parsed): # Si la fecha de pago no es NaN, se asigna a la nueva calificación
                            nueva_calificacion.FechaPago = fecha_parsed.to_pydatetime()
                    except Exception as e: # Si hay error, se pasa al siguiente try
                        print(f"[CARGAR_FACTOR] Error al parsear fecha: {e}") # Imprime el error de parseo de fecha
                        pass # Si hay error, se pasa al siguiente try
                
                # Secuencia evento usando pandas (se convierte la secuencia de evento a un entero)
                sec_eve = fila_limpia.get('SEC_EVE') or fila_limpia.get('Sec_Eve') or fila_limpia.get('sec_eve') or '' # Se obtiene el valor de la secuencia de evento
                if sec_eve: # Si la secuencia de evento no es None, se convierte a entero
                    try:
                        nueva_calificacion.SecuenciaEvento = pd.to_numeric(sec_eve, errors='raise').astype(int) # Se convierte la secuencia de evento a un entero
                    except (ValueError, TypeError, Exception):
                        print(f"[CARGAR_FACTOR] Advertencia: No se pudo convertir SecuenciaEvento '{sec_eve}' a entero en fila {fila_num}")
                        pass
                
                # Asignar factores (F8 a F37) usando pandas
                for i in range(8, 38): # Se recorre el rango de factores (F8 a F37)
                    factor_key = f'F{i}' # Se obtiene el nombre del factor
                    factor_value = fila_limpia.get(factor_key, '0.0') # Se obtiene el valor del factor
                    try:
                        # Usar pandas para convertir a numérico
                        factor_numeric = pd.to_numeric(factor_value, errors='coerce') # Se convierte el valor del factor a un número
                        if pd.isna(factor_numeric):
                            factor_decimal = Decimal(0) # Se asigna el valor de 0 al factor decimal
                        else:
                            factor_decimal = Decimal(str(factor_numeric)) # Se convierte el valor del factor a un número decimal
                            # Validar que el factor esté entre 0 y 1
                            if factor_decimal < 0: # Si el factor decimal es menor que 0, se asigna el valor de 0 al factor decimal
                                factor_decimal = Decimal(0) # Se asigna el valor de 0 al factor decimal
                            elif factor_decimal > 1: # Si el factor decimal es mayor que 1, se asigna el valor de 1 al factor decimal
                                factor_decimal = Decimal(1) # Se asigna el valor de 1 al factor decimal
                        setattr(nueva_calificacion, f'Factor{i:02d}', factor_decimal) # Se asigna el valor del factor a la nueva calificación
                    except Exception as e:
                        print(f"[CARGAR_FACTOR] Error al procesar factor {i}: {e}") # Imprime el error de procesamiento de factor
                        setattr(nueva_calificacion, f'Factor{i:02d}', Decimal(0)) # Se asigna el valor de 0 al factor
                
                nueva_calificacion.FechaAct = datetime.datetime.now() # Se asigna la fecha de actualización a la nueva calificación
                nueva_calificacion.save() # Se guarda la nueva calificación en la base de datos
                calificaciones_creadas += 1
                print(f"[CARGAR_FACTOR] Calificación {fila_num} guardada exitosamente") # Imprime el mensaje de guardado exitoso de la calificación
                
            except Exception as e:
                print(f"[CARGAR_FACTOR] Error en fila {fila_num}: {e}") # Imprime el error de la fila
                import traceback
                print(traceback.format_exc()) # Imprime el traceback de la excepción
                errores.append(f'Fila {fila_num}: {str(e)}')
                continue
        
        # Crear log de carga masiva
        if calificaciones_creadas > 0:
            _crear_log(current_user, 'Carga Masiva', documento_afectado=None, hash_archivo_csv=hash_archivo) # Se crea el log de carga masiva con el hash del archivo
            print(f"[CARGAR_FACTOR] Log creado para {calificaciones_creadas} calificaciones (hash: {hash_archivo})")
            
            # Registrar el archivo CSV procesado para evitar duplicados
            if hash_archivo:
                from .models import ArchivoCSV
                try:
                    archivo_csv = ArchivoCSV(
                        hash_archivo=hash_archivo,
                        nombre_archivo=nombre_archivo,
                        tipo='factor',
                        usuario=current_user,
                        total_filas=calificaciones_creadas
                    )
                    archivo_csv.save()
                    print(f"[CARGAR_FACTOR] Archivo CSV registrado: {nombre_archivo} (hash: {hash_archivo})")
                except Exception as e:
                    print(f"[CARGAR_FACTOR] Error al registrar archivo CSV: {e}")
        
        mensaje = f'Se crearon {calificaciones_creadas} calificación(es) exitosamente.' # Se crea el mensaje de creación de calificaciones exitosas         
        if errores:
            mensaje += f' Se encontraron {len(errores)} error(es).' # Se agrega el mensaje de errores a la variable mensaje
        
        print(f"[CARGAR_FACTOR] Proceso completado: {calificaciones_creadas} creadas, {len(errores)} errores") # Imprime el mensaje de proceso completado
        
        return JsonResponse({ # Se retorna un JSON con los datos de la carga masiva
            'success': True, # Se asigna el valor de True al JSON
            'total': calificaciones_creadas, # Se asigna el total de calificaciones creadas al JSON
            'errores': errores, # Se asigna el total de errores al JSON
            'message': mensaje # Se asigna el mensaje de creación de calificaciones exitosas al JSON
        }) # Se retorna un JSON con los datos de la carga masiva
        
    except Exception as e:
        print(f"[CARGAR_FACTOR] Error al cargar factores: {e}") # Imprime el error de carga masiva
        import traceback
        print(traceback.format_exc()) # Imprime el traceback de la excepción
        return JsonResponse({'success': False, 'error': f'Error al procesar: {str(e)}'}, status=500) # Se retorna un JSON con el error de procesamiento


# =====================================================================
# VISTAS DE CARGA MASIVA DE MONTOS
# =====================================================================
@require_POST
def cargar_monto_view(request):
    
    """
    Vista AJAX para cargar calificaciones desde CSV con montos.
    
    Procesa un CSV que contiene montos financieros.
    Si los factores ya están calculados, los guarda directamente.
    Si no, calcula los factores automáticamente: Factor = Monto / SumaBase
    
    Flujo:
    1. Recibe datos del CSV (después de previsualización y posible cálculo de factores)
    2. Valida cada fila
    3. Calcula factores si es necesario
    4. Crea calificaciones en MongoDB
    5. Crea log de carga masiva
    
    Argumentos:
        request: Objeto HttpRequest de Django (solo POST permitido)
        
    Returns (lo que devuelve la funcion):
        JsonResponse: JSON con cantidad de calificaciones creadas y errores encontrados
    """
    print("[CARGAR_MONTO] Iniciando carga de montos...") # Imprime el mensaje de inicio de carga de montos
    
    if 'user_id' not in request.session: # Si el usuario no está autenticado, retorna un error
        print("[CARGAR_MONTO] Error: No autenticado")
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401) # Se retorna un JSON con el error de no autenticado

    try:
        current_user = usuarios.objects.get(id=request.session['user_id']) # Se obtiene el usuario autenticado
        print(f"[CARGAR_MONTO] Usuario autenticado: {current_user.correo}")
    except usuarios.DoesNotExist:
        print("[CARGAR_MONTO] Error: Usuario no válido") # Imprime el error de usuario no válido
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401)

    try: 
        import pandas as pd # Importamos el modulo pandas para manejar datos en tablas  
        import json # Importamos el modulo json para manejar datos en formato JSON
        from decimal import Decimal # Importamos el modulo decimal para manejar números decimales
        
        print("[CARGAR_MONTO] Parseando JSON...") # Imprime el mensaje de parseo de JSON
        data = json.loads(request.body) # Se carga el JSON de la solicitud
        datos_csv = data.get('datos', []) # Se obtiene los datos del JSON
        hash_archivo = data.get('hash_archivo', '') # Se obtiene el hash del archivo
        nombre_archivo = data.get('nombre_archivo', 'archivo.csv') # Se obtiene el nombre del archivo
        
        print(f"[CARGAR_MONTO] Datos recibidos: {len(datos_csv)} filas") # Imprime el mensaje de datos recibidos
        print(f"[CARGAR_MONTO] Hash del archivo: {hash_archivo}") # Imprime el hash del archivo
        
        if not datos_csv: # Si no se recibieron datos, retorna un error
            print("[CARGAR_MONTO] Error: No se recibieron datos") # Imprime el error de no recibido de datos
            return JsonResponse({'success': False, 'error': 'No se recibieron datos'}, status=400) # Se retorna un JSON con el error de no recibido de datos
        
        # Verificar si este archivo ya fue procesado (doble verificación)
        if hash_archivo:
            from .models import ArchivoCSV
            archivo_existente = ArchivoCSV.objects(hash_archivo=hash_archivo).first()
            if archivo_existente:
                # Verificar si todavía existen calificaciones con este hash de archivo CSV
                calificaciones_existentes = Calificacion.objects(
                    Origen='csv',
                    hash_archivo_csv=hash_archivo
                ).count()
                
                print(f"[CARGAR_MONTO] Archivo duplicado encontrado. Calificaciones existentes con hash {hash_archivo}: {calificaciones_existentes}")
                
                # Si no hay calificaciones con ese hash, eliminar el registro de ArchivoCSV para permitir subirlo nuevamente
                if calificaciones_existentes == 0:
                    archivo_existente.delete()
                    print(f"[CARGAR_MONTO] Se eliminó el registro de ArchivoCSV porque no quedan calificaciones. Permitiendo subida.")
                else:
                    print(f"[CARGAR_MONTO] Error: Archivo duplicado detectado. Hash: {hash_archivo}")
                    return JsonResponse({
                        'success': False, 
                        'error': f'Este archivo ya fue procesado anteriormente el {archivo_existente.fecha_subida.strftime("%Y-%m-%d %H:%M:%S")} por {archivo_existente.usuario.correo} y todavía existen {calificaciones_existentes} calificación(es) creadas desde ese archivo.',
                        'duplicado': True
                    }, status=400)
        
        # Convertir a DataFrame de pandas para procesamiento más eficiente
        df = pd.DataFrame(datos_csv) # Se convierte el JSON a un dataframe de pandas
        
        # Limpiar nombres de columnas (eliminar espacios)
        df.columns = df.columns.str.strip() # Se eliminan los espacios de los nombres de las columnas
        
        # Eliminar filas completamente vacías
        df = df.dropna(how='all') # Se eliminan las filas completamente vacías
        
        calificaciones_creadas = 0 # Se inicializa la variable de calificaciones creadas
        errores = [] # Se inicializa la variable de errores
        
        # Iterar sobre el DataFrame
        for idx, row in df.iterrows():
            fila_num = idx + 2  # +2 porque idx empieza en 0 y la fila 1 es el encabezado (la primera fila es el encabezado)
            try:
                # Convertir la fila a diccionario
                fila = row.to_dict()
                
                # Convertir valores NaN a strings vacíos y limpiar
                fila_limpia = {} # Se crea un diccionario para la fila limpia
                for key, value in fila.items():
                    if pd.isna(value): # Si el valor es NaN, se asigna un string vacío
                        fila_limpia[key] = '' # Se asigna un string vacío al diccionario de la fila limpia
                    else: # Si el valor no es NaN, se convierte a string y se eliminan los espacios
                        fila_limpia[key] = str(value).strip() if value else '' # Se asigna el valor de la fila limpia al diccionario de la fila limpia
                
                # Debug: mostrar las claves disponibles en la primera fila
                if fila_num == 2:
                    print(f"[CARGAR_MONTO] Claves disponibles en CSV: {list(fila_limpia.keys())}") # Imprime las claves disponibles en el CSV
                    print(f"[CARGAR_MONTO] Primera fila completa: {fila_limpia}")
                    print(f"[CARGAR_MONTO] Ejercicio raw: '{fila_limpia.get('Ejercicio')}'") # Imprime el ejercicio raw
                    print(f"[CARGAR_MONTO] Mercado raw: '{fila_limpia.get('Mercado')}'") # Imprime el mercado raw
                    print(f"[CARGAR_MONTO] Instrumento raw: '{fila_limpia.get('Instrumento')}'") # Imprime el instrumento raw
                
                # Validar campos requeridos (buscar con diferentes variaciones)
                # Primero intentar obtener Ejercicio
                ejercicio = fila_limpia.get('Ejercicio') or fila_limpia.get('ejercicio') or ''
                mercado_raw = fila_limpia.get('Mercado') or fila_limpia.get('mercado') or ''
                instrumento = fila_limpia.get('Instrumento') or fila_limpia.get('instrumento') or ''
                
                # Normalizar mercado a los valores válidos (acciones, CFI, Fondos mutuos)
                mercado_normalizado = mercado_raw
                if mercado_raw:
                    mercado_lower = mercado_raw.lower().strip()
                    if mercado_lower == 'acciones' or mercado_lower == 'accion':
                        mercado_normalizado = 'acciones'
                    elif mercado_lower == 'cfi':
                        mercado_normalizado = 'CFI'
                    elif mercado_lower == 'fondos mutuos' or mercado_lower == 'fondosmutuos' or mercado_lower == 'fondo mutuo':
                        mercado_normalizado = 'Fondos mutuos'
                
                mercado = mercado_normalizado # Se asigna el valor del mercado normalizado a la variable mercado
                
                # Detectar si Ejercicio e Instrumento están intercambiados
                # Si Ejercicio contiene letras (como "ACC001") e Instrumento es numérico, intercambiar
                ejercicio_es_numero = False
                instrumento_es_numero = False
                ejercicio_tiene_letras = any(c.isalpha() for c in str(ejercicio)) if ejercicio else False
                
                try:
                    int(ejercicio)
                    ejercicio_es_numero = True
                except (ValueError, TypeError):
                    pass # Si hay error, se pasa al siguiente try
                
                try:
                    int(instrumento)
                    instrumento_es_numero = True
                except (ValueError, TypeError):
                    pass
                
                # Si Ejercicio no es numérico pero Instrumento sí, intercambiar
                # O si Ejercicio tiene letras (parece código de instrumento) e Instrumento es numérico (parece año)
                if (not ejercicio_es_numero and instrumento_es_numero) or (ejercicio_tiene_letras and instrumento_es_numero):
                    print(f"[CARGAR_MONTO] Advertencia: Ejercicio e Instrumento parecen estar intercambiados en fila {idx}. Ejercicio: '{ejercicio}', Instrumento: '{instrumento}'")
                    ejercicio, instrumento = instrumento, ejercicio
                    ejercicio_es_numero = True
                
                if not ejercicio or not mercado:
                    # Mostrar qué claves tiene la fila para ayudar a debuggear
                    claves_disponibles = ', '.join(fila.keys())
                    errores.append(f'Fila {idx}: Faltan campos requeridos (Ejercicio, Mercado). Claves disponibles: {claves_disponibles}')
                    continue
                
                # Validar y convertir Ejercicio a entero
                try:
                    ejercicio_int = int(ejercicio)
                except (ValueError, TypeError):
                    # Mostrar más información sobre el error
                    claves_disponibles = ', '.join(fila.keys())
                    errores.append(f'Fila {idx}: El campo Ejercicio debe ser un número entero. Valor recibido: "{ejercicio}". Instrumento recibido: "{instrumento}". Claves disponibles: {claves_disponibles}')
                    continue
                
                # Crear nueva calificación
                nueva_calificacion = Calificacion()
                nueva_calificacion.Ejercicio = ejercicio_int
                nueva_calificacion.Mercado = mercado
                nueva_calificacion.Instrumento = instrumento
                nueva_calificacion.Origen = 'csv'  # Normalizado a minúsculas para coincidir con el filtro
                nueva_calificacion.hash_archivo_csv = hash_archivo  # Guardar el hash del archivo CSV para relacionar la calificación con el archivo
                nueva_calificacion.Descripcion = fila_limpia.get('DESCRIPCION') or fila_limpia.get('Descripcion') or fila_limpia.get('descripcion') or ''
                
                # Fecha de pago usando pandas
                fecha_pago = fila_limpia.get('FEC_PAGO') or fila_limpia.get('Fec_Pago') or fila_limpia.get('fec_pago') or ''
                if fecha_pago:
                    try:
                        fecha_parsed = pd.to_datetime(fecha_pago, format='%Y-%m-%d', errors='coerce')
                        if not pd.isna(fecha_parsed):
                            nueva_calificacion.FechaPago = fecha_parsed.to_pydatetime()
                    except Exception as e:
                        print(f"[CARGAR_MONTO] Error al parsear fecha: {e}")
                        pass
                
                # Secuencia evento usando pandas
                sec_eve = fila_limpia.get('SEC_EVE') or fila_limpia.get('Sec_Eve') or fila_limpia.get('sec_eve') or ''
                if sec_eve:
                    try:
                        nueva_calificacion.SecuenciaEvento = pd.to_numeric(sec_eve, errors='raise').astype(int)
                    except (ValueError, TypeError, Exception):
                        print(f"[CARGAR_MONTO] Advertencia: No se pudo convertir SecuenciaEvento '{sec_eve}' a entero en fila {fila_num}")
                        pass
                
                # Verificar si ya tiene factores calculados (después de presionar "CALCULAR FACTORES")
                tiene_factores = any(f'F{i}' in fila_limpia for i in range(8, 38)) # Se verifica si ya tiene factores calculados
                
                if tiene_factores:
                    # Los factores ya están calculados, solo asignarlos usando pandas
                    for i in range(8, 38): # Se recorre el rango de factores (F8 a F37)
                        factor_key = f'F{i}' # Se obtiene el nombre del factor
                        factor_value = fila_limpia.get(factor_key, '0.0') # Se obtiene el valor del factor
                        try:
                            factor_numeric = pd.to_numeric(factor_value, errors='coerce') # Se convierte el valor del factor a un número
                            if pd.isna(factor_numeric):
                                factor_decimal = Decimal(0) # Se asigna el valor de 0 al factor decimal
                            else:
                                factor_decimal = Decimal(str(factor_numeric)) # Se convierte el valor del factor a un número decimal
                                if factor_decimal < 0:
                                    factor_decimal = Decimal(0) # Se asigna el valor de 0 al factor decimal
                                elif factor_decimal > 1:
                                    factor_decimal = Decimal(1) # Se asigna el valor de 1 al factor decimal
                            setattr(nueva_calificacion, f'Factor{i:02d}', factor_decimal) # Se asigna el valor del factor a la nueva calificación
                        except Exception as e:
                            print(f"[CARGAR_MONTO] Error al procesar factor {i}: {e}") # Imprime el error de procesamiento de factor
                            setattr(nueva_calificacion, f'Factor{i:02d}', Decimal(0)) # Se asigna el valor de 0 al factor
                    
                    # Si hay montos originales, guardarlos también usando pandas
                    suma_base = Decimal(0) # Se inicializa la variable de suma base     
                    for i in range(8, 38):
                        # Buscar la clave del monto (puede ser "F8 MONT" o "F8 M")
                        monto_key = None
                        for key in fila_limpia.keys():
                            if key.strip() == f'F{i} MONT' or key.strip() == f'F{i} M':
                                monto_key = key
                                break
                        
                        monto_value = fila_limpia.get(monto_key, '0.0') if monto_key else '0.0' # Se obtiene el valor del monto
                        try:
                            monto_numeric = pd.to_numeric(monto_value, errors='coerce') # Se convierte el valor del monto a un número
                            if pd.isna(monto_numeric):
                                monto_decimal = Decimal(0) # Se asigna el valor de 0 al monto decimal
                            else:
                                monto_decimal = Decimal(str(monto_numeric)) # Se convierte el valor del monto a un número decimal
                            setattr(nueva_calificacion, f'Monto{i:02d}', monto_decimal) # Se asigna el valor del monto a la nueva calificación
                            if i <= 19: # Se verifica si el monto es menor o igual a 19
                                suma_base += monto_decimal # Se suma el valor del monto a la suma base
                        except Exception as e:
                            print(f"[CARGAR_MONTO] Error al procesar monto {i}: {e}")
                            setattr(nueva_calificacion, f'Monto{i:02d}', Decimal(0))
                    
                    nueva_calificacion.SumaBase = suma_base # Se asigna el valor de la suma base a la nueva calificación
                else:
                    # Obtener montos y calcular suma base usando pandas
                    montos = []
                    suma_base = Decimal(0)
                    
                    for i in range(8, 38): # Se recorre el rango de montos (F8 a F37)
                        # Buscar la clave del monto (puede ser "F8 MONT" o "F8 M")
                        monto_key = None
                        for key in fila_limpia.keys():
                            if key.strip() == f'F{i} MONT' or key.strip() == f'F{i} M':
                                monto_key = key
                                break
                        
                        monto_value = fila_limpia.get(monto_key, '0.0') if monto_key else '0.0'
                        try:
                            monto_numeric = pd.to_numeric(monto_value, errors='coerce')
                            if pd.isna(monto_numeric):
                                monto_decimal = Decimal(0)
                            else:
                                monto_decimal = Decimal(str(monto_numeric))
                            montos.append(monto_decimal)
                            if i <= 19:  # Solo sumar del 8 al 19
                                suma_base += monto_decimal
                        except Exception as e:
                            print(f"[CARGAR_MONTO] Error al procesar monto {i}: {e}")
                            montos.append(Decimal(0))
                    
                    nueva_calificacion.SumaBase = suma_base # Se asigna el valor de la suma base a la nueva calificación
                    
                    # Guardar montos
                    for i in range(8, 38):
                        setattr(nueva_calificacion, f'Monto{i:02d}', montos[i - 8]) # Se asigna el valor del monto a la nueva calificación
                    
                    # Calcular factores 
                    if suma_base > 0: # Se verifica si la suma base es mayor que 0
                        EIGHT_PLACES = Decimal('0.00000001')
                        for i in range(8, 38):
                            factor = (montos[i - 8] / suma_base).quantize(EIGHT_PLACES)
                            if factor > 1: # Se verifica si el factor es mayor que 1
                                factor = Decimal(1) # Se asigna el valor de 1 al factor
                            setattr(nueva_calificacion, f'Factor{i:02d}', factor) # Se asigna el valor del factor a la nueva calificación
                    else:
                        for i in range(8, 38):
                            setattr(nueva_calificacion, f'Factor{i:02d}', Decimal(0))
                
                nueva_calificacion.FechaAct = datetime.datetime.now()
                nueva_calificacion.save()
                calificaciones_creadas += 1
                print(f"[CARGAR_MONTO] Calificación {fila_num} guardada exitosamente")
                
            except Exception as e:
                print(f"[CARGAR_MONTO] Error en fila {fila_num}: {e}")
                import traceback
                print(traceback.format_exc())
                errores.append(f'Fila {fila_num}: {str(e)}')
                continue
        
        # Crear log de carga masiva (se crea el log de carga masiva)
        if calificaciones_creadas > 0:
            _crear_log(current_user, 'Carga Masiva', documento_afectado=None, hash_archivo_csv=hash_archivo)
            print(f"[CARGAR_MONTO] Log creado para {calificaciones_creadas} calificaciones (hash: {hash_archivo})")
            
            # Registrar el archivo CSV procesado para evitar duplicados
            if hash_archivo:
                from .models import ArchivoCSV
                try:
                    archivo_csv = ArchivoCSV(
                        hash_archivo=hash_archivo,
                        nombre_archivo=nombre_archivo,
                        tipo='monto',
                        usuario=current_user,
                        total_filas=calificaciones_creadas
                    )
                    archivo_csv.save()
                    print(f"[CARGAR_MONTO] Archivo CSV registrado: {nombre_archivo} (hash: {hash_archivo})")
                except Exception as e:
                    print(f"[CARGAR_MONTO] Error al registrar archivo CSV: {e}")
        
        mensaje = f'Se crearon {calificaciones_creadas} calificación(es) exitosamente.'
        if errores:
            mensaje += f' Se encontraron {len(errores)} error(es).'
        
        print(f"[CARGAR_MONTO] Proceso completado: {calificaciones_creadas} creadas, {len(errores)} errores")
        
        return JsonResponse({ # Se retorna un JSON con los datos de la carga masiva
            'success': True,
            'total': calificaciones_creadas, # Se asigna el total de calificaciones creadas al JSON
            'errores': errores, # Se asigna el total de errores al JSON
            'message': mensaje # Se asigna el mensaje de creación de calificaciones exitosas al JSON
        })
        
    except Exception as e: # Si hay error, se imprime el error y se retorna un JSON con el error de procesamiento
        print(f"[CARGAR_MONTO] Error al cargar montos: {e}")
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': f'Error al procesar: {str(e)}'}, status=500)


# =====================================================================
# VISTAS DE CALCULAR FACTORES MASIVOS
# =====================================================================
@require_POST
def calcular_factores_masivo_view(request):
    """Vista para calcular factores desde montos en carga masiva"""
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        import json
        from decimal import Decimal
        
        data = json.loads(request.body)
        datos_csv = data.get('datos', [])
        
        if not datos_csv:
            return JsonResponse({'success': False, 'error': 'No se recibieron datos'}, status=400)
        
        datos_calculados = []
        
        for fila in datos_csv:
            fila_calculada = fila.copy()
            
            # Obtener montos y calcular suma base
            montos = []
            suma_base = Decimal(0)
            
            for i in range(8, 38):
                monto_key = f'F{i} MONT' if f'F{i} MONT' in fila else f'F{i} M'
                monto_value = fila.get(monto_key, '0.0')
                try:
                    monto_decimal = Decimal(str(monto_value))
                    montos.append(monto_decimal)
                    if i <= 19:  # Solo sumar del 8 al 19
                        suma_base += monto_decimal
                except:
                    montos.append(Decimal(0))
            
            # Calcular factores
            if suma_base > 0:
                EIGHT_PLACES = Decimal('0.00000001')
                for i in range(8, 38):
                    factor = (montos[i - 8] / suma_base).quantize(EIGHT_PLACES)
                    if factor > 1:
                        factor = Decimal(1)
                    fila_calculada[f'F{i}'] = str(factor)
            else:
                for i in range(8, 38):
                    fila_calculada[f'F{i}'] = '0.0'
            
            datos_calculados.append(fila_calculada)
        
        return JsonResponse({
            'success': True,
            'datos_calculados': datos_calculados
        })
        
    except Exception as e:
        print(f"Error al calcular factores masivo: {e}")
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': f'Error al calcular: {str(e)}'}, status=500)


@require_GET
def obtener_logs_calificacion_view(request, calificacion_id):
    """Vista para obtener los logs de una calificación específica"""
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401)

    try:
        # Obtener la calificación
        calificacion = Calificacion.objects.get(id=calificacion_id)
        
        # Obtener información básica de la calificación
        calificacion_info = {
            'ejercicio': calificacion.Ejercicio or '',
            'instrumento': calificacion.Instrumento or '',
            'mercado': calificacion.Mercado or ''
        }
        
        # Obtener logs relacionados con esta calificación
        logs_raw = Log.objects(iddocumento=calificacion).order_by('-fecharegistrada')
        logs_procesados = []
        
        for l in logs_raw:
            # Actor (usuario que ejecutó la acción)
            actor_correo = getattr(l, "correoElectronico", "N/A")
            actor_id = "N/A"
            actor_nombre = "N/A"
            
            if hasattr(l, "Usuarioid") and l.Usuarioid:
                actor_id_obj = _extraer_object_id(l.Usuarioid)
                if actor_id_obj:
                    actor_id = str(actor_id_obj)
                    try:
                        actor_usuario = usuarios.objects.get(id=actor_id_obj)
                        actor_nombre = actor_usuario.nombre
                    except usuarios.DoesNotExist:
                        pass
            
            # Obtener cambios detallados si existen
            cambios_detallados = None
            if hasattr(l, "cambios_detallados") and l.cambios_detallados:
                try:
                    import json
                    cambios_detallados = json.loads(l.cambios_detallados)
                except:
                    cambios_detallados = None
            
            logs_procesados.append({
                "fecha": getattr(l, "fecharegistrada", None).isoformat() if getattr(l, "fecharegistrada", None) else None,
                "actor_correo": actor_correo,
                "actor_id": actor_id,
                "actor_nombre": actor_nombre,
                "accion": getattr(l, "accion", "N/A"),
                "cambios_detallados": cambios_detallados
            })
        
        return JsonResponse({
            'success': True,
            'logs': logs_procesados,
            'calificacion_info': calificacion_info
        })
        
    except Calificacion.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Calificación no encontrada'}, status=404)
    except Exception as e:
        print(f"Error al obtener logs: {e}")
        return JsonResponse({'success': False, 'error': f'Error al obtener logs: {str(e)}'}, status=500)