"""
===========================================================
Este archivo contiene todas las vistas
Las vistas manejan la lógica de negocio, interactúan con la base de datos y devuelven respuestas HTML o JSON.

Estructura de las vistas xd:
 Funciones auxiliares: Funciones de utilidad compartidas
 Vistas de autenticación: Login, logout
 Vistas de navegación: Home, administración
 Vistas de usuarios: Crear, modificar, eliminar usuarios
 Vistas de calificaciones: Crear, modificar, eliminar, buscar calificaciones
 Vistas de factores/montos: Calcular factores, guardar montos
 Vistas de carga masiva: Cargar CSV, previsualizar archivos
 Vistas de logs: Ver registros de auditoría
"""

# IMPORTACIONES
# ======================================
import json      # Para manejar datos JSON en las respuestas de API
import bcrypt    # Para hashear contraseñas de forma segura
import re        # Para expresiones regulares - usado en _extraer_object_id() para parsear DBRef
import os        # Para operaciones del sistema de archivos (rutas, extensiones)
import datetime  # Para manejar fechas y horas
import csv       # Para exportar datos a CSV
from django.shortcuts import render, redirect  # render: renderizar templates HTML | redirect: redirigir a otras URLs
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseServerError, HttpResponse  # Respuestas HTTP: Forbidden(403), JSON, ServerError(500), HttpResponse para CSV estas respuestas son para los errores por ejemplo cuando no se encuentra el usuario o cuando hay un error en el servidor
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


# ===================================
# FUNCION AUXILIAR: EXTRAER OBJECTID
# ===================================
# Extrae el ObjectId desde un DBRef, ObjectId o cualquier otro tipo.
# Se usa para obtener el ID de documentos referenciados en MongoDB.
# Retorna el string del ObjectId o None si no puede extraerlo.

#glosario: 
# DBRef: DBRef es la referencia al documento en MongoDB.
# ObjectId: ObjectId es la id por defecto de MongoDB único para un documento en MongoDB.
# try-except: try-except es una estructura de control de errores que permite manejar errores de forma segura.
# except: except es una estructura de control de errores que permite manejar errores de forma segura.
# Exception: Exception es una clase que representa una excepción
# no_dereference(): no_dereference() es una función que evita cargar documentos completos (más rápido), pero devuelve DBRef
# regex: regex es una expresión regular que se usa para buscar patrones en un texto por ejemplo para buscar el ObjectId en un string

# ===================================
def _extraer_object_id(valor):
# ===================================
    """
    Extrae el ObjectId desde un DBRef, ObjectId o cualquier otro tipo.
    Retorna el string del ObjectId o None si no puede extraerlo.
    
    ESTA FUNCION FUNCIONA PORQUE:
    - MongoDB usa ObjectIds para identificar documentos
    - Cuando usamos no_dereference() en MongoEngine, obtenemos DBRef en lugar de objetos completos 
    - Los DBRef tienen el ObjectId dentro, pero necesitamos extraerlo como string PORQUE MongoDB guarda strings, no bytes
    - Esta función maneja todos los casos posibles: DBRef, ObjectId directo, string, etc.
    
    Argumentos:
        valor: Puede ser un DBRef, ObjectId, string, o cualquier objeto que contenga un ID
        
    Returns (lo que devuelve la funcion):
        str: String del ObjectId si se puede extraer, None en caso contrario
    """
    # Hacemos la validación inicial PORQUE: si el valor es None, False, 0, "", etc, retornamos None Esto evita procesar valores inválidos y previene errores
    if not valor:
        return None
    
    # Usamos try-except porque ObjectId() puede lanzar excepciones si el formato es inválido 
    # Esto porque es  mejor capturar la excepción que validar manualmente todos los casos

    # ===================================
    # CASO 1: Si es un DBRef (cuando usas no_dereference() en MongoEngine, ESTO ES PARA EL DBREF)
    # ===================================
    try:
        # CASO 1: Si es un DBRef (cuando usas no_dereference() en MongoEngine)
        # LOGICA: Los DBRef tienen el ObjectId en el atributo 'id'
        # POR QUÉ: no_dereference() evita cargar documentos completos (más rápido), pero devuelve DBRef
        #codigo:
        if hasattr(valor, 'id'):
            # Obtenemos el ID del DBRef
            obj_id = valor.id
            
            # Si el ID es un ObjectId directamente, lo convertimos a string esto porque necesitamos el string para guardarlo en JSON o compararlo
            if isinstance(obj_id, ObjectId):
                return str(obj_id)
            
            # Si el ID ya es un string, validamos que sea un ObjectId válido esto porque ObjectId() lanzará excep si el formato es inválido (24 caracteres hex)
            elif isinstance(obj_id, str):
                ObjectId(obj_id)  # Validar formato - si es inválido, lanza excepción
                return obj_id  # Si llegamos aquí, es válido, retornamos el string
            
            # Si es otro tipo (int, etc.), lo convertimos a string
            # POR QUÉ: Algunos sistemas pueden usar otros tipos, mejor ser flexible
            else:
                return str(obj_id)

        # ===================================
        # CASO 2: Si ya es un ObjectId directamente (sin DBRef) 
        # ===================================
        # LOGICA: Simplemente lo convertimos a string
        #porque: porque si ya es objectId no necesitamos hacer nada con el
        #codigo:

        elif isinstance(valor, ObjectId): #aca hacemos la validación de si es un ObjectId directamente
            return str(valor) #aca convertimos el ObjectId a string
        

        # ===================================
        # CASO 3: Si es una string que representa un ObjectId
        # ===================================
        # LoGICA: Puede ser un string simple o una representación de DBRef como string
        #codigo:

        elif isinstance(valor, str): #aca hacemos la validación de si es un string que representa un ObjectId
            # Si el string contiene "DBRef" y "ObjectId", es una representación de DBRef
            # PORQUE: A veces MongoDB devuelve DBRef como string

            if "DBRef" in valor and "ObjectId" in valor:
                # Usamos regex para extraer el ObjectId del string
                # PATRON: ObjectId donde son 24 caracteres hexadecimales por ejemplo: ObjectId('665a43210000000000000000')
                # POR QUE: Los ObjectIds siempre tienen 24 caracteres hexadecimales
                match = re.search(r"ObjectId\('([a-f0-9]{24})'\)", valor)
                if match:
                    # match.group(1) es el primer grupo capturado (el ID sin ObjectId)
                    return match.group(1)
            
            # Si no es un DBRef string, intentamos validar que sea un ObjectId válido
            # POR QUE: ObjectId() lanzará excepción si el formato es inválido
            ObjectId(valor)  # Si es inválido, lanza excepcion aqui
            return valor  # si es valido, volvemos el string original
        

        # ===================================
        # CASO 4: Si tiene atributo pk (primary key en algunos objetos) 
        # ===================================
        # LOGICA: Algunos objetos MongoEngine usan 'pk' en lugar de 'id'
        #FLUJOxd: Si tiene atributo pk, convertimos el pk a string y lo retornamos esto se logra usando el str para convertirlo a string
        #por ejemplo: si tenemos un objeto con el atributo pk = 123, y usamos str(valor.pk) nos devolvera el string "123"
        #codigo:

        elif hasattr(valor, 'pk'): #aca hacemos la validación de si tiene atributo pk
            return str(valor.pk) #aca convertimos el pk a string esto se logra porque pk es el id del objeto y utilizamnos str para convertirlo a string
        

        # ===================================
        # CASO 5: Último recurso convertir a string y buscar DBRef esto es para cuando no coincide con ningun caso anterior
        # ===================================
        # LÓGICA: Si no coincide con ningún caso anterior, intentamos convertir a string
        # POR QUE: Algunos objetos pueden tener representación string que contenga el ID
        #FLUJOxd: Si no coincide con ningun caso anterior, convertimos el valor a string}
        # y lo retornamos esto se logra usando el str para convertirlo a string
        #codigo:
        
        else:
            str_valor = str(valor)  # Convertimos a string
            
            # Si el string contiene DBRef, intentamos extraer el ObjectId
            if "DBRef" in str_valor and "ObjectId" in str_valor:
                match = re.search(r"ObjectId\('([a-f0-9]{24})'\)", str_valor)
                if match:
                    return match.group(1)
            
            # Si no encontramos DBRef, retornamos el string tal cual
            # POR QUÉ: Puede ser un ID válido en formato string
            return str_valor
    
    # Si ocurre cualquier excepción (ObjectId inválido, etc), la capturamos
    # POR QUE: Es mejor retornar None que dejar que la excepción se propague
    except Exception as e:
        # Imprimimos el error para debugging, pero no interrumpimos el flujo
        print(f"Error al extraer ObjectId: {e}, valor: {valor}")
        return None  # Retornamos None para indicar que no se pudo extraer el ID



# ===================================
# FUNCION AUXILIAR: GUARDAR FOTO DE PERFIL
# =========================================
# Guarda la foto de perfil del usuario y retorna la ruta.
# Valida el tamaño y formato del archivo, redimensiona la imagen si es muy grande.
def _guardar_foto_perfil(archivo, usuario_id):
    """
    Guarda la foto de perfil del usuario y retorna la ruta.
    Redimensiona la imagen si es muy grande (máximo 500x500px).
    
    POR QUÉ ESTA FUNCIÓN ES NECESARIA:
    - Necesitamos validar archivos antes de guardarlos (seguridad)
    - Redimensionar imágenes grandes ahorra espacio en disco
    - Nombres únicos evitan sobrescribir fotos de otros usuarios
    - Guardamos ruta relativa en MongoDB, no la ruta absoluta (portabilidad)
    
    Argumentos:
        archivo: Archivo de imagen subido por el usuario
        usuario_id: ID del usuario para crear un nombre único
        
    Returns (lo que devuelve la funcion):
        str: Ruta relativa de la foto guardada (ej: 'fotos_perfil/usuario_123_foto.jpg')
        
    Raises (excepciones que puede lanzar la funcion):
        ValueError: Si el archivo es muy grande o tiene formato inválido
    """
    # Validación inicial: si no hay archivo, retornamos None
    # POR QUÉ: La foto de perfil es opcional, no todos los usuarios tienen foto
    if not archivo:
        return None
    
    # Validación de tamaño: máximo 5MB
    # POR QUÉ: Archivos muy grandes consumen mucho espacio y tiempo de carga
    # CÁLCULO: 5 * 1024 * 1024 = 5,242,880 bytes = 5MB
    # LÓGICA: Si el tamaño excede el límite, lanzamos ValueError para que la vista lo maneje
    if archivo.size > 5 * 1024 * 1024:
        raise ValueError("La imagen es demasiado grande. Máximo 5MB.")
    
    # Validación de formato de archivo
    # os.path.splitext() separa nombre y extensión: ("archivo", ".jpg")
    # [1] obtiene la extensión, .lower() la convierte a minúsculas para comparar
    # POR QUÉ: "JPG" y "jpg" deben tratarse igual
    extension = os.path.splitext(archivo.name)[1].lower()
    
    # Solo permitimos formatos de imagen comunes y seguros
    # POR QUÉ: Evitamos archivos ejecutables disfrazados de imágenes
    if extension not in ['.jpg', '.jpeg', '.png', '.gif']:
        raise ValueError("Formato de imagen no válido. Use JPG, PNG o GIF.")
    
    # Construir ruta del directorio donde se guardarán las fotos
    # settings.MEDIA_ROOT es la ruta base configurada en settings.py
    # / 'fotos_perfil' usa Path de Python para concatenar rutas de forma segura
    # POR QUÉ: Path maneja diferencias entre Windows (\) y Linux (/)
    media_dir = settings.MEDIA_ROOT / 'fotos_perfil'
    
    # Crear directorio si no existe
    # parents=True: crea directorios padre si no existen
    # exist_ok=True: no lanza error si el directorio ya existe
    # POR QUÉ: En la primera ejecución, el directorio no existe y debe crearse
    media_dir.mkdir(parents=True, exist_ok=True)
    
    # Generar nombre único del archivo
    # Formato: "usuario_{id}_{nombre_original}"
    # POR QUÉ: El ID del usuario garantiza unicidad, evita sobrescribir fotos de otros usuarios
    nombre_archivo = f"usuario_{usuario_id}_{archivo.name}"
    
    # Construir ruta completa del archivo (directorio + nombre)
    ruta_completa = media_dir / nombre_archivo
    
    # Guardar archivo en disco
    # 'wb+' = write binary + (permite lectura y escritura)
    # POR QUÉ: Las imágenes son binarias, no texto
    # with open() asegura que el archivo se cierre automáticamente
    with open(ruta_completa, 'wb+') as destino:
        # archivo.chunks() lee el archivo en pedazos (chunks)
        # POR QUÉ: Archivos grandes no caben en memoria completa, se leen por partes
        for chunk in archivo.chunks():
            destino.write(chunk)  # Escribe cada pedazo al archivo en disco
    
    # Redimensionar imagen si es necesario
    # HAS_PIL es True si Pillow está instalado, False si no
    # POR QUÉ: Pillow es opcional, la app debe funcionar sin él (pero sin redimensionar)
    if HAS_PIL:
        try:
            # Abrir imagen con Pillow
            img = Image.open(ruta_completa)
            
            # Verificar si alguna dimensión excede 500px
            # POR QUÉ: Imágenes grandes ocupan mucho espacio y tardan en cargar
            if img.width > 500 or img.height > 500:
                # thumbnail() redimensiona manteniendo proporción
                # (500, 500) es el tamaño máximo, la imagen puede ser más pequeña
                # LANCZOS es un algoritmo de alta calidad para redimensionar
                # POR QUÉ: Mantiene buena calidad visual al reducir tamaño
                img.thumbnail((500, 500), Image.Resampling.LANCZOS)
                
                # Guardar imagen redimensionada, sobrescribiendo la original
                # optimize=True: optimiza el tamaño del archivo
                # quality=85: balance entre calidad y tamaño (100 = máxima calidad, más pesado)
                # POR QUÉ: 85% de calidad es imperceptible para el ojo humano pero reduce tamaño
                img.save(ruta_completa, optimize=True, quality=85)
        except Exception as e:
            # Si falla la redimensionación, solo imprimimos error pero no fallamos
            # POR QUÉ: La imagen ya está guardada, la redimensionación es opcional
            print(f"Error al redimensionar imagen: {e}")
    else:
        # Si Pillow no está instalado, informamos pero continuamos
        # POR QUÉ: La app debe funcionar aunque no se redimensionen imágenes
        print("Pillow no está instalado. Las imágenes no se redimensionarán automáticamente.")
    
    # Retornar ruta relativa (no absoluta)
    # Formato: "fotos_perfil/usuario_123_foto.jpg"
    # POR QUÉ: La ruta relativa es portable entre diferentes servidores
    # Si usáramos ruta absoluta como "C:/proyecto/media/fotos_perfil/...", no funcionaría en otro servidor
    return f"fotos_perfil/{nombre_archivo}"



# FUNCIONES AUXILIARES: HASH DE CONTRASEÑAS
# ==========================================
# Funciones para hashear y verificar contraseñas usando bcrypt
# Bcrypt es un algoritmo de hashing seguro y ampliamente usado

def _hash_password(password):
    """
    Hashea una contraseña usando bcrypt.
    
    POR QUÉ ESTA FUNCIÓN ES CRÍTICA:
    - NUNCA debemos guardar contraseñas en texto plano (seguridad)
    - bcrypt es un algoritmo de hashing seguro y lento (dificulta ataques de fuerza bruta)
    - Cada hash incluye un "salt" aleatorio único (misma contraseña = diferentes hashes)
    - Esto protege contra ataques de diccionario y rainbow tables
    
    CÓMO FUNCIONA:
    1. Genera un salt aleatorio único
    2. Combina salt + contraseña y los hashea
    3. El resultado incluye el salt, así que no necesitamos guardarlo por separado
    
    Argumentos:
        password: Contraseña en texto plano
        
    Returns (lo que devuelve la funcion):
        str: Contraseña hasheada en formato bcrypt
    """
    # Validación: si no hay contraseña, retornamos None
    # POR QUÉ: Algunos usuarios pueden no tener contraseña (aunque no debería pasar)
    if not password:
        return None
    
    # Generar salt aleatorio único
    # POR QUÉ: El salt hace que cada hash sea único, incluso para la misma contraseña
    # Ejemplo: "password123" puede generar "$2b$12$abc..." o "$2b$12$xyz..." (diferentes)
    # Esto protege contra ataques que comparan hashes pre-calculados
    salt = bcrypt.gensalt()
    
    # Hashear la contraseña combinada con el salt
    # password.encode('utf-8'): convierte string a bytes (bcrypt requiere bytes)
    # bcrypt.hashpw(): combina salt + password y genera el hash
    # El resultado es bytes, no string
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    # Convertir hash de bytes a string para guardarlo en MongoDB
    # POR QUÉ: MongoDB guarda strings, no bytes
    return hashed.decode('utf-8')

def _check_password(password, hashed_password):
    """
    Verifica si una contraseña coincide con su hash usando bcrypt.
    
    POR QUÉ ESTA FUNCIÓN ES NECESARIA:
    - No podemos "deshashear" un hash (es unidireccional)
    - Para verificar, debemos hashear la contraseña ingresada y comparar
    - bcrypt.checkpw() hace esto de forma segura y eficiente
    
    CÓMO FUNCIONA:
    1. Toma el hash guardado (que incluye el salt original)
    2. Hashea la contraseña ingresada con el mismo salt
    3. Compara ambos hashes (si coinciden, la contraseña es correcta)
    
    Argumentos:
        password: Contraseña en texto plano a verificar
        hashed_password: Contraseña hasheada almacenada en la base de datos
        
    Returns (lo que devuelve la funcion):
        bool: True si la contraseña coincide, False en caso contrario
    """
    # Validación: si falta alguno de los dos, no podemos verificar
    # POR QUÉ: Necesitamos ambos para comparar
    if not password or not hashed_password:
        return False
    
    try:
        # bcrypt.checkpw() compara la contraseña con el hash de forma segura
        # password.encode('utf-8'): convierte string a bytes
        # hashed_password.encode('utf-8'): convierte hash string a bytes
        # Retorna True si coinciden, False si no
        # POR QUÉ: Usa comparación constante en tiempo (previene timing attacks)
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        # Si hay cualquier error (formato inválido, etc.), retornamos False
        # POR QUÉ: Es más seguro asumir que la contraseña es incorrecta que lanzar excepción
        return False





# FUNCIÓN AUXILIAR: CREAR LOG 
# ============================
# Guarda un registro de log con información sobre la acción realizada.
# Se usa para auditoría de todas las operaciones del sistema.
def _crear_log(usuario_obj, accion_str, documento_afectado=None, usuario_afectado=None, cambios_detallados=None, hash_archivo_csv=None):
    """
    Guarda un registro de log con información sobre la acción realizada.
    
    POR QUÉ ESTA FUNCIÓN ES IMPORTANTE:
    - Auditoría: registra quién hizo qué y cuándo
    - Seguridad: permite rastrear acciones sospechosas
    - Debugging: ayuda a entender qué pasó cuando algo falla
    - Cumplimiento: muchas regulaciones requieren logs de auditoría
    
    CÓMO FUNCIONA:
    1. Convierte cambios detallados a JSON (si existen)
    2. Crea objeto Log con toda la información
    3. Guarda en MongoDB
    4. Si falla, solo imprime advertencia (no interrumpe el flujo principal)
    
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
        # Inicializar cambios_json como None
        # POR QUÉ: Si no hay cambios, guardamos None en lugar de string vacío
        cambios_json = None
        
        # Si hay cambios detallados, los convertimos a JSON
        # POR QUÉ: MongoDB puede guardar JSON strings, pero es más eficiente guardarlo como string
        if cambios_detallados:
            import json
            # json.dumps() convierte lista/diccionario a string JSON
            # default=str: si encuentra tipos no serializables (Decimal, datetime), los convierte a string
            # POR QUÉ: Decimal y datetime no son JSON nativos, necesitan conversión
            cambios_json = json.dumps(cambios_detallados, default=str)
        
        # Crear objeto Log con todos los datos
        # Usuarioid: referencia al usuario que hizo la acción (DBRef en MongoDB)
        # correoElectronico: guardamos el correo también (por si el usuario se elimina después)
        # accion: tipo de acción ("Crear Calificacion", "Modificar Usuario", etc.)
        # iddocumento: referencia a la calificación afectada (si aplica)
        # usuario_afectado: referencia al usuario afectado (si aplica)
        # cambios_detallados: JSON string con los cambios específicos
        # hash_archivo_csv: hash del archivo CSV para cargas masivas
        nuevo_log = Log(
            Usuarioid=usuario_obj,
            correoElectronico=usuario_obj.correo,
            accion=accion_str,
            iddocumento=documento_afectado,
            usuario_afectado=usuario_afectado,
            cambios_detallados=cambios_json,
            hash_archivo_csv=hash_archivo_csv
        )
        
        # Guardar el log en MongoDB
        # POR QUÉ: MongoEngine requiere .save() para persistir en la base de datos
        nuevo_log.save()
        
        # Imprimir confirmación (útil para debugging)
        print(f"Log guardado correctamente: {accion_str} por {usuario_obj.correo}")
    
    except Exception as e:
        # Si falla al guardar el log, solo imprimimos advertencia
        # POR QUÉ: El log es importante pero no crítico - no queremos que un error de log
        # interrumpa la operación principal (ej: crear calificación)
        # Si el log falla, la acción principal debe continuar
        print(f"¡¡ADVERTENCIA!! Falló al guardar el log: {e}")



# =====================================================================
# VISTAS DE NAVEGACIÓN Y AUTENTICACIÓN
# Vistas que manejan la navegación y autenticación del usuario.
# Manejan el login, logout, home, etc.
# =====================================================================

def listar_usuarios(request):
    """
    Vista para listar todos los usuarios del sistema.
    
    POR QUÉ ESTA FUNCIÓN EXISTE:
    - Muestra una lista de todos los usuarios registrados
    - Permite ver información básica de usuarios
    - No requiere autenticación (puede ser útil para debugging)
    
    CÓMO FUNCIONA:
    1. Obtiene todos los usuarios de MongoDB
    2. Renderiza el template listar.html con la lista
    3. El template muestra los usuarios en una tabla o lista
    
    Argumentos:
        request: Objeto HttpRequest de Django
        
    Returns (lo que devuelve la funcion):
        HttpResponse: Renderiza el template listar.html con la lista de usuarios
    """
    # Obtener todos los usuarios de la base de datos MongoDB
    # usuarios.objects.all() consulta la colección 'usuarios' y retorna todos los documentos
    # POR QUÉ: Necesitamos todos los usuarios para mostrarlos en la lista
    todos_los_usuarios = usuarios.objects.all()
    
    # Renderizar el template con la lista de usuarios
    # render() combina el template HTML con los datos
    # 'prueba/listar.html' es la ruta del template
    # {'usuarios': todos_los_usuarios} pasa la lista de usuarios al template
    # POR QUÉ: El template necesita los datos para mostrarlos
    return render(request, 'prueba/listar.html', {'usuarios': todos_los_usuarios})



# =====================================================================
# VISTAS DE INICIO DE SESIÓN
# =====================================================================

def login_view(request):
    """
    Vista para el inicio de sesión de usuarios.
    
    POR QUÉ ESTA VISTA ES IMPORTANTE:
    - Es el punto de entrada al sistema (seguridad)
    - Maneja autenticación de usuarios (verificación de credenciales)
    - Crea sesiones para mantener al usuario logueado
    - Previene acceso no autorizado al sistema
    
    CÓMO FUNCIONA LA AUTENTICACIÓN:
    1. GET: Muestra formulario de login
    2. POST: Valida credenciales
       - Busca usuario por correo en MongoDB
       - Compara contraseña hasheada con bcrypt
       - Si es correcta, crea sesión y redirige a home
       - Si es incorrecta, muestra error
    
    FLUJO COMPLETO:
    1. Usuario accede a /login/ (GET) y ve formulario
    2. Usuario ingresa correo y contraseña y envía formulario (POST)
    3. Sistema valida y si es correcto crea sesión y redirige a home
    4. Si es incorrecto muestra error en el formulario
    
    Argumentos:
        request: Objeto HttpRequest de Django (contiene datos de la petición HTTP)
        
    Returns (lo que devuelve la funcion):
        HttpResponse: Renderiza login.html o redirige a home si las credenciales son correctas
    """
    # Verificar si el usuario ya está autenticado
    # request.session es un diccionario que Django mantiene entre peticiones
    # 'user_id' se guarda cuando el usuario inicia sesión exitosamente
    # POR QUÉ: Evita que usuarios ya logueados vean el formulario de login
    if 'user_id' in request.session:
        # Si ya tiene sesión activa, redirigir directamente a home
        # redirect('home') busca la URL con name='home' en urls.py
        return redirect('home')

    # Crear formulario vacío para mostrar en la página
    # LoginForm es un formulario Django que valida correo y contraseña
    # POR QUÉ: Django maneja validación automática (correo válido, campos requeridos, etc.)
    form = LoginForm()
    
    # Inicializar variable de error como None
    # POR QUÉ: Si no hay error, no mostramos mensaje. Si hay error, mostramos el mensaje
    error = None

    # Verificar el método HTTP de la petición
    # GET: Usuario accede a la página (ver formulario)
    # POST: Usuario envía el formulario (procesar login)
    if request.method == 'POST':
        # Crear formulario con los datos enviados en el POST
        # request.POST contiene todos los campos del formulario enviado
        form = LoginForm(request.POST)
        
        # Validar el formulario
        # is_valid() verifica:
        # - Campos requeridos están presentes
        # - Correo tiene formato válido
        # - Contraseña no está vacía
        if form.is_valid():
            # Obtener datos limpios del formulario
            # cleaned_data contiene los datos ya validados y procesados por Django
            # POR QUÉ: Django limpia y valida los datos automáticamente
            correo_usuario = form.cleaned_data['correo']
            contrasena_usuario = form.cleaned_data['contrasena']

            # Intentar buscar el usuario en la base de datos
            # POR QUÉ: Usamos try-except porque .get() lanza excepción si no encuentra el usuario
            try:
                # Buscar usuario por correo electrónico
                # usuarios.objects.get() busca un documento en MongoDB que coincida
                # Si no encuentra, lanza usuarios.DoesNotExist
                user = usuarios.objects.get(correo=correo_usuario)
                
                # Verificar si la contraseña ingresada coincide con la guardada
                # _check_password() compara la contraseña en texto plano con el hash guardado
                # POR QUÉ: No podemos comparar directamente porque la contraseña está hasheada
                # Si la contraseña NO coincide, establecemos user = None
                if not _check_password(contrasena_usuario, user.contrasena):
                    user = None
                    
            except usuarios.DoesNotExist:
                # Si el usuario no existe en la base de datos, establecer user = None
                # POR QUÉ: No queremos revelar si el correo existe o no (seguridad)
                # Si decimos "correo no existe" vs "contraseña incorrecta", damos información a atacantes
                user = None

            # Verificar si encontramos un usuario válido con contraseña correcta
            if user:
                # Crear sesión del usuario
                # request.session es un diccionario que Django guarda en cookies/BD
                # 'user_id': ID del usuario (lo usamos para identificar al usuario en otras vistas)
                # 'user_nombre': Nombre del usuario (para mostrar en la interfaz)
                # POR QUÉ: La sesión permite que el usuario permanezca logueado entre peticiones
                # Django maneja automáticamente las cookies y el almacenamiento de sesión
                request.session['user_id'] = str(user.id)  # Convertir ObjectId a string
                request.session['user_nombre'] = user.nombre
                
                # Redirigir a la página principal (home)
                # redirect('home') busca la URL con name='home' en urls.py
                return redirect('home')
            else:
                # Si el usuario no existe o la contraseña es incorrecta
                # Mostrar mensaje genérico (no revelar cuál fue el error específico)
                # POR QUÉ: Seguridad - no queremos decir "correo no existe" o "contraseña incorrecta"
                # Un atacante podría usar esto para descubrir correos válidos
                error = "Correo o contraseña incorrectos."
    
    # Renderizar el template de login con el formulario y el error (si existe)
    # render() combina el template HTML con los datos (form, error)
    # 'prueba/login.html' es la ruta del template (Django busca en templates/prueba/)
    # {'form': form, 'error': error} son las variables disponibles en el template
    return render(request, 'prueba/login.html', {'form': form, 'error': error})



# =====================================================================
# VISTAS DE DASHBOARD
# =====================================================================

def home_view(request):
    """
    Vista principal del dashboard (página de inicio).
    
    POR QUÉ ESTA VISTA ES IMPORTANTE:
    - Es la página principal después del login
    - Muestra todas las calificaciones del sistema
    - Permite filtrar calificaciones por diferentes criterios
    - Proporciona datos en JSON para que JavaScript los use dinámicamente
    
    CÓMO FUNCIONA:
    1. Verifica que el usuario esté autenticado
    2. Obtiene filtros de la URL (mercado, origen, período)
    3. Normaliza los valores de filtros (acepta variaciones como "Acciones", "acciones", etc.)
    4. Construye query de MongoDB con los filtros
    5. Carga calificaciones de la base de datos
    6. Serializa a JSON para JavaScript
    7. Renderiza el template con los datos
    
    Funcionalidades:
    - Verifica autenticación del usuario
    - Permite filtrar calificaciones por mercado, origen y período
    - Muestra calificaciones en formato JSON para JavaScript
    
    Argumentos:
        request: Objeto HttpRequest de Django
        
    Returns (lo que devuelve la funcion):
        HttpResponse: Renderiza home.html con las calificaciones filtradas
    """
    # Verificar autenticación del usuario
    # POR QUÉ: Solo usuarios autenticados pueden ver el dashboard
    # Si no tiene sesión, redirigir a login
    if 'user_id' not in request.session:
        return redirect('login')

    # Obtener información del usuario actual
    # POR QUÉ: Necesitamos saber si es admin para mostrar opciones especiales
    try:
        # Buscar usuario en MongoDB usando el ID de la sesión
        # request.session['user_id'] es un string, pero MongoDB necesita ObjectId
        # MongoEngine convierte automáticamente el string a ObjectId
        current_user = usuarios.objects.get(id=request.session['user_id'])
        
        # Obtener rol del usuario (True = admin, False = usuario normal)
        # POR QUÉ: Los admins ven opciones adicionales en la interfaz
        is_admin = current_user.rol
    except usuarios.DoesNotExist:
        # Si el usuario no existe (fue eliminado mientras estaba logueado)
        # Limpiar sesión y redirigir a login
        # POR QUÉ: La sesión tiene un ID inválido, debemos limpiarla
        request.session.flush()
        return redirect('login')

    # Inicializar lista vacía de calificaciones
    # POR QUÉ: Si no hay filtros o no hay calificaciones, la lista estará vacía
    calificaciones = []
    
    # Procesar solo si es método GET (cargar página o aplicar filtros)
    # GET se usa cuando el usuario accede a la URL o envía filtros desde el formulario
    if request.method == 'GET':
        # Obtener parámetros de filtro de la URL
        # request.GET es un diccionario con los parámetros de la URL (?mercado=acciones&origen=csv)
        # .get('mercado', '') obtiene el valor o '' si no existe
        mercado_raw = request.GET.get('mercado', '')
        origen = request.GET.get('origen', '')
        periodo = request.GET.get('periodo', '')
        
        # NORMALIZACIÓN DE MERCADO
        # POR QUÉ: Los usuarios pueden escribir "Acciones", "acciones", "ACCIONES", etc.
        # Necesitamos convertir todo a un formato estándar para la base de datos
        mercado_normalizado = mercado_raw
        
        # Solo normalizar si hay valor y no es "Todos"
        if mercado_raw and mercado_raw != 'Todos':
            # Convertir a minúsculas y eliminar espacios al inicio/final
            # .lower() convierte "Acciones" a "acciones"
            # .strip() elimina espacios de " acciones " dejando "acciones"
            mercado_lower = mercado_raw.lower().strip()
            
            # Comparar con variaciones posibles y asignar valor normalizado
            # POR QUÉ: Aceptamos "accion" (singular) y "acciones" (plural)
            if mercado_lower == 'acciones' or mercado_lower == 'accion':
                mercado_normalizado = 'acciones'
            elif mercado_lower == 'cfi':
                mercado_normalizado = 'CFI'
            # Aceptamos variaciones: "fondos mutuos", "fondosmutuos", "fondo mutuo"
            elif mercado_lower == 'fondos mutuos' or mercado_lower == 'fondosmutuos' or mercado_lower == 'fondo mutuo':
                mercado_normalizado = 'Fondos mutuos'
            else:
                # Si no coincide con ningún valor conocido, mantener el original
                # POR QUÉ: Puede ser un valor válido que no conocíamos
                mercado_normalizado = mercado_raw
        
        # NORMALIZACIÓN DE ORIGEN
        # Similar a mercado, normalizamos "CSV", "csv", "Csv" a "csv"
        origen_normalizado = origen
        if origen:
            origen_lower = origen.lower().strip()
            if origen_lower == 'csv':
                origen_normalizado = 'csv'
            elif origen_lower == 'corredor':
                origen_normalizado = 'corredor'
        
        # CONSTRUIR QUERY DE MONGODB
        # query es un diccionario que se pasa a Calificacion.objects(**query)
        # Solo agregamos filtros que tienen valor
        query = {}
        
        # Agregar filtro de mercado si tiene valor y no es "Todos"
        if mercado_normalizado and mercado_normalizado != 'Todos':
            query['Mercado'] = mercado_normalizado
        
        # Agregar filtro de origen si tiene valor
        if origen_normalizado:
            query['Origen'] = origen_normalizado
        
        # Agregar filtro de período (año) si tiene valor
        if periodo:
            try:
                # Convertir período a entero, ejemplo: "2024" se convierte a 2024
                # POR QUÉ: En MongoDB, Ejercicio es IntField, necesita número, no string
                periodo_int = int(periodo)
                query['Ejercicio'] = periodo_int
            except ValueError:
                # Si no es un número válido, ignorar el filtro
                # POR QUÉ: No queremos que un período inválido rompa la consulta
                pass
        
        # CARGAR CALIFICACIONES DE MONGODB
        # Si hay filtros en query, aplicar filtros
        # Si query está vacío, cargar todas las calificaciones
        if query:
            # Calificacion.objects(**query) aplica los filtros
            # **query expande el diccionario, ejemplo: {'Mercado': 'acciones'} se convierte en Mercado='acciones'
            # .order_by('-FechaAct') ordena por fecha de actualización descendente (más recientes primero)
            # El signo '-' significa descendente
            calificaciones = Calificacion.objects(**query).order_by('-FechaAct')
        else:
            # Si no hay filtros, cargar TODAS las calificaciones
            # POR QUÉ: Al cargar la página por primera vez, queremos mostrar todas las calificaciones
            # Si no mostramos nada, el dashboard se ve vacío y confunde al usuario
            calificaciones = Calificacion.objects().order_by('-FechaAct')

    # SERIALIZAR CALIFICACIONES A JSON
    # POR QUÉ: JavaScript necesita los datos en formato JSON para mostrarlos dinámicamente
    # El template HTML recibe tanto los objetos MongoEngine como el JSON string
    import json
    calificaciones_data = []  # Lista que contendrá diccionarios con datos de cada calificación
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

@require_GET
def buscar_calificaciones_view(request):
    """
    Vista AJAX para buscar calificaciones según filtros.
    
    POR QUÉ ESTA FUNCIÓN ES NECESARIA:
    - Permite buscar calificaciones dinámicamente sin recargar la página
    - JavaScript puede llamar esta función y actualizar la interfaz
    - Retorna JSON en lugar de HTML, más eficiente para actualizaciones dinámicas
    - Similar a home_view pero optimizada para AJAX
    
    CÓMO FUNCIONA:
    1. Recibe filtros desde la URL (mercado, origen, período)
    2. Normaliza los valores de filtros
    3. Construye query de MongoDB
    4. Busca calificaciones con los filtros
    5. Serializa a JSON y retorna
    
    DIFERENCIA CON home_view:
    - home_view: renderiza HTML completo
    - buscar_calificaciones_view: retorna solo JSON (para AJAX)
    
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
    # Verificar autenticación del usuario
    # POR QUÉ: Solo usuarios autenticados pueden buscar calificaciones
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        # Obtener parámetros de filtro de la URL
        # request.GET contiene los parámetros de la URL (?mercado=acciones&origen=csv)
        # .get('mercado', '') obtiene el valor o string vacío si no existe
        # .strip() elimina espacios al inicio y final
        mercado_raw = request.GET.get('mercado', '').strip()
        origen = request.GET.get('origen', '').strip()
        periodo = request.GET.get('periodo', '').strip()

        # NORMALIZAR MERCADO
        # Convertir variaciones a valores estándar
        # POR QUÉ: Los usuarios pueden escribir "Acciones", "acciones", "ACCIONES", etc.
        mercado_normalizado = mercado_raw
        if mercado_raw:
            # Convertir a minúsculas y eliminar espacios
            mercado_lower = mercado_raw.lower().strip()
            if mercado_lower == 'acciones' or mercado_lower == 'accion':
                mercado_normalizado = 'acciones'
            elif mercado_lower == 'cfi':
                mercado_normalizado = 'CFI'
            elif mercado_lower == 'fondos mutuos' or mercado_lower == 'fondosmutuos' or mercado_lower == 'fondo mutuo':
                mercado_normalizado = 'Fondos mutuos'

        # NORMALIZAR ORIGEN
        # Similar a mercado, normalizar variaciones
        origen_normalizado = origen
        if origen:
            origen_lower = origen.lower().strip()
            if origen_lower == 'csv':
                origen_normalizado = 'csv'
            elif origen_lower == 'corredor':
                origen_normalizado = 'corredor'
        
        # CONSTRUIR QUERY DE MONGODB
        # query es un diccionario que se pasa a Calificacion.objects(**query)
        query = {}
        
        # Agregar filtro de mercado si tiene valor y no es "Todos"
        if mercado_normalizado and mercado_normalizado != 'Todos':
            query['Mercado'] = mercado_normalizado
        
        # Agregar filtro de origen si tiene valor
        if origen_normalizado:
            query['Origen'] = origen_normalizado
        
        # Agregar filtro de período si tiene valor
        if periodo:
            try:
                # Convertir período a entero
                # POR QUÉ: En MongoDB, Ejercicio es IntField, necesita número
                periodo_int = int(periodo)
                query['Ejercicio'] = periodo_int
            except ValueError:
                # Si no es un número válido, ignorar el filtro
                # POR QUÉ: No queremos que un período inválido rompa la consulta
                pass

        # BUSCAR CALIFICACIONES EN MONGODB
        # Si hay filtros, aplicar filtros; si no, obtener todas
        if query:
            # Aplicar filtros y ordenar por fecha descendente
            calificaciones = Calificacion.objects(**query).order_by('-FechaAct')
        else:
            # Si no hay filtros, obtener todas las calificaciones
            calificaciones = Calificacion.objects().order_by('-FechaAct')

        # SERIALIZAR CALIFICACIONES A JSON
        # Convertir objetos MongoEngine a diccionarios para JSON
        calificaciones_data = []
        
        # Iterar sobre cada calificación encontrada
        for cal in calificaciones:
            # Obtener ID de la calificación
            # Convertir ObjectId a string para JSON
            cal_id = str(cal.id) if cal.id else ''
            
            # Validar que tenga ID
            # POR QUÉ: Las calificaciones sin ID no se pueden usar
            if not cal_id:
                print(f"ADVERTENCIA: Calificación sin ID: {cal}")
                continue  # Saltar esta calificación
            
            # Crear diccionario con datos de la calificación
            # or '' convierte None a string vacío para evitar errores en JSON
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
                'factores': {}  # Diccionario para los factores
            }
            
            # Agregar todos los factores del 8 al 37
            # POR QUÉ: JavaScript necesita todos los factores para mostrar en la interfaz
            for i in range(8, 38):
                # Construir nombre del campo: "Factor08", "Factor09", etc.
                field_name = f'Factor{i:02d}'
                
                # Obtener valor del factor del objeto calificación
                # getattr() obtiene el atributo o 0.0 si no existe
                valor = getattr(cal, field_name, 0.0)
                
                # Convertir a string para JSON
                # Si el valor es None o 0, usar '0.0'
                cal_data['factores'][field_name] = str(valor) if valor else '0.0'
            
            # Agregar la calificación procesada a la lista
            calificaciones_data.append(cal_data)

        # Retornar respuesta JSON con las calificaciones encontradas
        return JsonResponse({
            'success': True,  # Indica que la operación fue exitosa
            'calificaciones': calificaciones_data,  # Lista de calificaciones
            'total': len(calificaciones_data)  # Cantidad total de resultados
        })

    except Exception as e:
        # Si ocurre cualquier error, capturarlo y retornar error en JSON
        # POR QUÉ: Mejor retornar error claro que dejar que la excepción se propague
        print(f"Error al buscar calificaciones: {e}")
        return JsonResponse({'success': False, 'error': f'Error al buscar: {str(e)}'}, status=500) #retornamos el error en formato JSON


@require_GET
def exportar_calificaciones_view(request):
    """
    Vista para exportar calificaciones a CSV según IDs seleccionados.
    
    POR QUÉ ESTA FUNCIÓN ES NECESARIA:
    - Permite exportar calificaciones para análisis externo
    - Los usuarios pueden descargar datos en formato CSV (compatible con Excel)
    - Útil para reportes y análisis financieros
    - Puede exportar calificaciones específicas o todas
    
    CÓMO FUNCIONA:
    1. Recibe IDs de calificaciones desde la URL (opcional)
    2. Si hay IDs, busca solo esas calificaciones
    3. Si no hay IDs, exporta todas las calificaciones
    4. Crea archivo CSV con encabezados y datos
    5. Retorna el archivo como descarga
    
    Permite exportar calificaciones específicas pasando sus IDs como parámetros.
    Si no se pasan IDs, exporta todas las calificaciones.
    
    Retorna un archivo CSV descargable con las calificaciones seleccionadas y sus factores.
    
    Argumentos:
        request: Objeto HttpRequest de Django (solo GET permitido)
        - ids: Lista de IDs de calificaciones separados por comas (opcional)
        
    Returns (lo que devuelve la funcion):
        HttpResponse: Archivo CSV con las calificaciones
    """
    # Verificar autenticación del usuario
    # POR QUÉ: Solo usuarios autenticados pueden exportar datos
    if 'user_id' not in request.session:
        return HttpResponseForbidden('No autenticado')
    
    try:
        # Obtener parámetro 'ids' de la URL
        # Formato esperado: ?ids=id1,id2,id3
        # .strip() elimina espacios
        ids_param = request.GET.get('ids', '').strip()
        
        # Verificar si se proporcionaron IDs específicos
        if ids_param:
            # Separar IDs por comas y limpiar espacios
            # split(',') divide el string en lista: "id1,id2" -> ["id1", "id2"]
            # [id.strip() for id in ...] elimina espacios de cada ID
            # if id.strip() filtra IDs vacíos
            ids_list = [id.strip() for id in ids_param.split(',') if id.strip()]
            
            try:
                # Convertir strings a ObjectId para MongoDB
                # ObjectId() valida el formato y convierte el string
                # POR QUÉ: MongoDB requiere ObjectId, no strings
                object_ids = [ObjectId(id) for id in ids_list]
                
                # Buscar solo las calificaciones con esos IDs
                # id__in busca documentos cuyo ID esté en la lista
                # order_by('-FechaAct') ordena por fecha descendente
                calificaciones = Calificacion.objects(id__in=object_ids).order_by('-FechaAct')
            except Exception as e:
                # Si algún ID tiene formato inválido, retornar error
                print(f"Error al convertir IDs: {e}")
                return HttpResponseServerError('Error: IDs inválidos')
        else:
            # Si no hay IDs, exportar todas las calificaciones
            calificaciones = Calificacion.objects().order_by('-FechaAct')
        
        # CREAR RESPUESTA HTTP CON TIPO CSV
        # content_type='text/csv' indica que es un archivo CSV
        # charset='utf-8' permite caracteres especiales (tildes, ñ, etc.)
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        
        # Configurar nombre del archivo descargable
        # Content-Disposition: attachment hace que el navegador descargue el archivo
        # filename define el nombre del archivo
        # datetime.now().strftime() genera timestamp: 20240115_143022
        # POR QUÉ: Cada exportación tiene nombre único basado en fecha/hora
        response['Content-Disposition'] = f'attachment; filename="calificaciones_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        # Crear escritor CSV
        # csv.writer() escribe datos en formato CSV
        # response es el destino donde se escribe
        writer = csv.writer(response)
        
        # ESCRIBIR ENCABEZADOS DEL CSV
        # Primera fila contiene los nombres de las columnas
        headers = [
            'ID', 'Ejercicio', 'Mercado', 'Origen', 'Instrumento', 'Fecha Pago', 
            'Secuencia Evento', 'Descripcion', 'Fecha Act', 'Dividendo', 
            'Valor Historico', 'Factor Actualizacion', 'Anho', 'ISFUT'
        ]
        
        # Agregar encabezados de factores F8 a F37
        # POR QUÉ: Cada factor necesita su propia columna en el CSV
        for i in range(8, 38):
            headers.append(f'Factor{i:02d}')
        
        # Escribir la fila de encabezados
        writer.writerow(headers)
        
        # ESCRIBIR DATOS DE CADA CALIFICACIÓN
        # Cada calificación se convierte en una fila del CSV
        for cal in calificaciones:
            # Crear fila con datos básicos de la calificación
            # or '' convierte None a string vacío para evitar errores
            row = [
                str(cal.id) if cal.id else '',  # ID como string
                cal.Ejercicio or '',  # Año del ejercicio
                cal.Mercado or '',  # Tipo de mercado
                cal.Origen or '',  # Origen de los datos
                cal.Instrumento or '',  # Código del instrumento
                cal.FechaPago.strftime('%Y-%m-%d') if cal.FechaPago else '',  # Fecha formateada
                cal.SecuenciaEvento or '',  # Secuencia del evento
                cal.Descripcion or '',  # Descripción
                cal.FechaAct.strftime('%Y-%m-%d %H:%M:%S') if cal.FechaAct else '',  # Fecha de actualización
                str(cal.Dividendo) if cal.Dividendo else '0.0',  # Dividendo
                str(cal.ValorHistorico) if cal.ValorHistorico else '0.0',  # Valor histórico
                str(cal.FactorActualizacion) if cal.FactorActualizacion else '0.0',  # Factor de actualización
                cal.Anho or '',  # Año alternativo
                'True' if cal.ISFUT else 'False'  # Indicador booleano como string
            ]
            
            # Agregar todos los factores F8 a F37 a la fila
            for i in range(8, 38):
                field_name = f'Factor{i:02d}'
                valor = getattr(cal, field_name, 0.0)
                # Convertir a string, usar '0.0' si es None
                row.append(str(valor) if valor else '0.0')
            
            # Escribir la fila completa en el CSV
            writer.writerow(row)
        
        # Retornar la respuesta HTTP con el archivo CSV
        # El navegador descargará automáticamente el archivo
        return response
        
    except Exception as e:
        # Si ocurre cualquier error, capturarlo y retornar error
        print(f"Error al exportar calificaciones: {e}")
        return HttpResponseServerError(f'Error al exportar: {str(e)}')


# =====================================================================
# VISTAS DE CERRAR SESIÓN
# =====================================================================

def logout_view(request):
    """
    Vista para cerrar sesión del usuario.
    
    POR QUÉ ESTA FUNCIÓN ES NECESARIA:
    - Permite al usuario cerrar sesión de forma segura
    - Elimina todos los datos de la sesión (seguridad)
    - Previene que otros usuarios accedan a la cuenta si la sesión no se cierra
    
    CÓMO FUNCIONA:
    1. Elimina todos los datos de la sesión del usuario
    2. Redirige a la página de login
    
    Elimina todos los datos de la sesión y redirige al login.
    
    Argumentos:
        request: Objeto HttpRequest de Django
        
    Returns (lo que devuelve la funcion):
        HttpResponseRedirect: Redirige a la página de login
    """
    # Eliminar todos los datos de la sesión
    # flush() borra user_id, user_nombre y cualquier otro dato guardado
    # POR QUÉ: Seguridad - no queremos dejar datos de sesión después del logout
    request.session.flush()
    
    # Redirigir a la página de login
    # redirect('login') busca la URL con name='login' en urls.py
    return redirect('login')


# =====================================================================
# VISTAS DE INFORMACIÓN
# =====================================================================

def contacto_view(request):
    """
    Vista para mostrar la página de contacto de Nuam.
    
    POR QUÉ ESTA FUNCIÓN EXISTE:
    - Muestra información de contacto de la empresa
    - Página pública accesible sin autenticación
    - Proporciona información de contacto para usuarios
    
    CÓMO FUNCIONA:
    1. Renderiza el template contacto.html
    2. No requiere autenticación (página pública)
    
    Muestra información de contacto de la empresa Nuam.
    No requiere autenticación.
    
    Argumentos:
        request: Objeto HttpRequest de Django
        
    Returns (lo que devuelve la funcion):
        HttpResponse: Renderiza contacto.html con información de contacto
    """
    # Renderizar template de contacto
    # No se pasan datos adicionales, el template tiene la información estática
    # POR QUÉ: Es una página informativa simple que no necesita datos dinámicos
    return render(request, 'prueba/contacto.html')


# =====================================================================
# VISTAS DE CALIFICACIONES
# =====================================================================

def ingresar_view(request):
    """
    Vista para ingresar una nueva calificación o modificar una existente.
    
    POR QUÉ ESTA FUNCIÓN ES CRÍTICA:
    - Es el punto de entrada para crear y modificar calificaciones
    - Maneja la validación y normalización de datos
    - Registra todos los cambios para auditoría
    - Es la primera parte de un flujo de dos pasos (datos básicos, luego factores)
    
    CÓMO FUNCIONA:
    1. GET: Muestra formulario vacío o con datos iniciales
    2. POST: Valida datos, normaliza valores, crea o actualiza calificación
    3. Si es creación: retorna ID para abrir segundo modal de factores
    4. Si es actualización: registra cambios y retorna datos actualizados
    
    FLUJO COMPLETO:
    1. Usuario llena formulario básico (modal 1)
    2. Sistema valida y guarda calificación básica
    3. Sistema retorna calificacion_id
    4. JavaScript abre segundo modal con calificacion_id
    5. Usuario ingresa factores en segundo modal
    
    Esta vista maneja el primer modal (datos básicos de la calificación).
    Después de guardar, se abre un segundo modal para ingresar factores.
    
    Argumentos:
        request: Objeto HttpRequest de Django
        
    Returns (lo que devuelve la funcion):
        JsonResponse: Si es POST y éxito, retorna JSON con el ID de la calificación
        HttpResponse: Si es GET, renderiza el formulario
    """
    # Verificar autenticación del usuario
    # POR QUÉ: Solo usuarios autenticados pueden crear/modificar calificaciones
    if 'user_id' not in request.session:
        return redirect('login')

    # Obtener usuario actual de la base de datos
    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
    except usuarios.DoesNotExist:
        # Si el usuario no existe, limpiar sesión y redirigir
        # POR QUÉ: La sesión tiene un ID inválido
        request.session.flush()
        return redirect('login')

    # Procesar formulario si es método POST
    if request.method == 'POST':
        # Crear formulario con datos del POST
        form = CalificacionModalForm(request.POST)
        
        # Validar formulario
        if form.is_valid():
            # Copiar datos limpios del formulario
            # .copy() crea una copia para poder modificar sin afectar el original
            cleaned_data = form.cleaned_data.copy()
            
            # CONVERTIR FECHA DE PAGO
            # Si FechaPago viene como string, convertirla a DateTime
            # POR QUÉ: MongoDB necesita DateTime, no string
            if 'FechaPago' in cleaned_data and cleaned_data['FechaPago']:
                if isinstance(cleaned_data['FechaPago'], str):
                    from datetime import datetime
                    try:
                        # strptime() convierte string a DateTime
                        # '%Y-%m-%d' es el formato esperado: "2024-01-15"
                        cleaned_data['FechaPago'] = datetime.strptime(cleaned_data['FechaPago'], '%Y-%m-%d')
                    except:
                        # Si el formato es inválido, ignorar (no romper el flujo)
                        pass
            
            # VALIDAR SECUENCIA DE EVENTO
            # La secuencia debe ser mayor a 10000
            # POR QUÉ: Regla de negocio - las secuencias válidas empiezan en 10001
            if 'SecuenciaEvento' in cleaned_data and cleaned_data['SecuenciaEvento']:
                if cleaned_data['SecuenciaEvento'] <= 10000:
                    return JsonResponse({'success': False, 'error': 'La secuencia de evento debe ser mayor a 10,000.'}, status=400)
            
            # NORMALIZAR MERCADO
            # Convertir variaciones a valores estándar
            mercado_raw = cleaned_data.get('Mercado', '')
            if mercado_raw:
                mercado_lower = mercado_raw.lower().strip()
                if mercado_lower == 'acciones' or mercado_lower == 'accion':
                    cleaned_data['Mercado'] = 'acciones'
                elif mercado_lower == 'cfi':
                    cleaned_data['Mercado'] = 'CFI'
                elif mercado_lower == 'fondos mutuos' or mercado_lower == 'fondosmutuos' or mercado_lower == 'fondo mutuo':
                    cleaned_data['Mercado'] = 'Fondos mutuos'
            
            # NORMALIZAR ORIGEN
            # Convertir variaciones a valores estándar
            origen_raw = cleaned_data.get('Origen', 'corredor')
            if origen_raw:
                origen_lower = origen_raw.lower().strip()
                if origen_lower == 'csv':
                    cleaned_data['Origen'] = 'csv'
                elif origen_lower == 'corredor' or origen_lower == 'manual':
                    cleaned_data['Origen'] = 'corredor'
            else:
                # Si no hay origen, usar 'corredor' como valor por defecto
                cleaned_data['Origen'] = 'corredor'
            
            # DETERMINAR SI ES CREACIÓN O ACTUALIZACIÓN
            # Si hay calificacion_id en el POST, es actualización
            # Si no hay calificacion_id, es creación nueva
            calificacion_id = request.POST.get('calificacion_id')
            
            if calificacion_id:
                # ACTUALIZAR CALIFICACIÓN EXISTENTE
                try:
                    # Obtener la calificación existente de MongoDB
                    calificacion = Calificacion.objects.get(id=calificacion_id)
                    
                    # Inicializar lista para registrar cambios detallados
                    # POR QUÉ: Necesitamos registrar qué cambió para el log de auditoría
                    cambios_detallados = []
                    
                    # Flag para saber si realmente hubo cambios
                    # POR QUÉ: Solo actualizamos FechaAct si hubo cambios reales
                    campos_actualizados = False
                    
                    # Recorrer todos los campos del formulario
                    for key, value in cleaned_data.items():
                        # Solo procesar campos que fueron enviados en el POST original
                        # POR QUÉ: Algunos campos pueden estar en cleaned_data pero no fueron modificados
                        if key in request.POST:
                            # Obtener el valor actual del campo en la calificación
                            # getattr() obtiene el atributo o None si no existe
                            valor_actual = getattr(calificacion, key, None)
                            
                            # FUNCIÓN AUXILIAR: Formatear valores para comparación
                            # Convierte diferentes tipos a string para comparar y mostrar
                            def formatear_valor(val):
                                if val is None:
                                    return None
                                # Si es datetime, convertir a string formateado
                                if isinstance(val, datetime.datetime):
                                    return val.strftime('%Y-%m-%d %H:%M:%S')
                                # Si es booleano, convertir a "Sí" o "No"
                                if isinstance(val, bool):
                                    return 'Sí' if val else 'No'
                                # Para otros tipos, convertir a string
                                return str(val)
                            
                            # Formatear valores para comparación y para el log
                            valor_anterior_str = formatear_valor(valor_actual)
                            valor_nuevo_str = formatear_valor(value)
                            
                            # Flag para saber si este campo específico cambió
                            cambio_realizado = False
                            
                            # COMPARAR Y ACTUALIZAR SEGÚN EL TIPO DE DATO
                            # Cada tipo de dato se compara de forma diferente
                            
                            # Para campos booleanos (True/False)
                            if isinstance(value, bool):
                                if valor_actual != value:
                                    # Actualizar el campo en el objeto
                                    setattr(calificacion, key, value)
                                    campos_actualizados = True
                                    cambio_realizado = True
                            
                            # Para campos numéricos (int, float)
                            elif isinstance(value, (int, float)):
                                if valor_actual != value:
                                    setattr(calificacion, key, value)
                                    campos_actualizados = True
                                    cambio_realizado = True
                            
                            # Para campos string
                            elif isinstance(value, str):
                                # Solo actualizar si el string no está vacío y es diferente
                                # POR QUÉ: No queremos sobrescribir con strings vacíos
                                if value.strip() != '' and valor_actual != value:
                                    setattr(calificacion, key, value)
                                    campos_actualizados = True
                                    cambio_realizado = True
                            
                            # Para fechas y otros tipos
                            elif value is not None:
                                if valor_actual != value:
                                    setattr(calificacion, key, value)
                                    campos_actualizados = True
                                    cambio_realizado = True
                            
                            # Si hubo cambio, registrar en la lista de cambios
                            # POR QUÉ: Necesitamos estos datos para el log de auditoría
                            if cambio_realizado:
                                cambios_detallados.append({
                                    'campo': key,  # Nombre del campo que cambió
                                    'valor_anterior': valor_anterior_str,  # Valor antes del cambio
                                    'valor_nuevo': valor_nuevo_str  # Valor después del cambio
                                })
                    
                    # ASIGNAR EVENTOCAPITAL AUTOMÁTICAMENTE
                    # Si EventoCapital está vacío pero hay SecuenciaEvento, usar SecuenciaEvento
                    # POR QUÉ: Regla de negocio - EventoCapital puede derivarse de SecuenciaEvento
                    if (not calificacion.EventoCapital or calificacion.EventoCapital == '') and calificacion.SecuenciaEvento:
                        calificacion.EventoCapital = str(calificacion.SecuenciaEvento)
                        # Si no había cambios previos, marcar que hubo cambio
                        if not campos_actualizados:
                            campos_actualizados = True
                    
                    # GUARDAR CAMBIOS EN MONGODB
                    # Solo actualizar FechaAct si realmente hubo cambios
                    # POR QUÉ: No queremos actualizar la fecha si no hubo modificaciones reales
                    if campos_actualizados:
                        # Actualizar fecha de última modificación
                        calificacion.FechaAct = datetime.datetime.now()
                        
                        # Guardar los cambios en MongoDB
                        calificacion.save()
                        
                        # Crear log de auditoría con los cambios detallados
                        # Si hay cambios, los incluimos; si no, pasamos None
                        _crear_log(current_user, 'Modificar Calificacion', documento_afectado=calificacion, cambios_detallados=cambios_detallados if cambios_detallados else None)
                    else:
                        # Si no hubo cambios, crear log sin cambios detallados
                        # POR QUÉ: Aún así registramos que se intentó modificar
                        _crear_log(current_user, 'Modificar Calificacion', documento_afectado=calificacion)
                    
                    # Retornar JSON con los datos actualizados
                    # JavaScript usará estos datos para actualizar la interfaz
                    return JsonResponse({
                        'success': True,
                        'calificacion_id': str(calificacion.id),
                        'data': {
                            'mercado': calificacion.Mercado or '',
                            'origen': calificacion.Origen or '',
                            'instrumento': calificacion.Instrumento or '',
                            'evento_capital': calificacion.EventoCapital or str(calificacion.SecuenciaEvento) if calificacion.SecuenciaEvento else '',
                            'fecha_pago': calificacion.FechaPago.strftime('%Y-%m-%d') if calificacion.FechaPago else '',
                            'secuencia': calificacion.SecuenciaEvento or '',
                            'anho': calificacion.Anho or calificacion.Ejercicio or '',
                            'valor_historico': str(calificacion.ValorHistorico or 0.0),
                            'descripcion': calificacion.Descripcion or ''
                        }
                    })
                except Calificacion.DoesNotExist:
                    # Si la calificación no existe, retornar error
                    return JsonResponse({'success': False, 'error': 'Calificación no encontrada.'}, status=404)
            else:
                # CREAR NUEVA CALIFICACIÓN
                # Si no hay calificacion_id, es una creación nueva
                
                # Crear nuevo objeto Calificacion con los datos del formulario
                # **cleaned_data expande el diccionario como argumentos: Mercado='acciones', Ejercicio=2024, etc.
                nueva_calificacion = Calificacion(**cleaned_data)
                
                # Asignar EventoCapital automáticamente si no está definido
                # Si EventoCapital está vacío pero hay SecuenciaEvento, usar SecuenciaEvento
                if not nueva_calificacion.EventoCapital and nueva_calificacion.SecuenciaEvento:
                    nueva_calificacion.EventoCapital = str(nueva_calificacion.SecuenciaEvento)
                
                # Guardar la nueva calificación en MongoDB
                # save() persiste el documento y genera un ObjectId automáticamente
                nueva_calificacion.save()
                
                # Crear log de auditoría de la creación
                _crear_log(current_user, 'Crear Calificacion', documento_afectado=nueva_calificacion)
                
                # Retornar JSON con el ID de la calificación
                # JavaScript usará este ID para abrir el segundo modal de factores
                return JsonResponse({
                    'success': True,
                    'calificacion_id': str(nueva_calificacion.id),
                    'data': {
                        'mercado': nueva_calificacion.Mercado or '',
                        'origen': nueva_calificacion.Origen or '',
                        'instrumento': nueva_calificacion.Instrumento or '',
                        'evento_capital': nueva_calificacion.EventoCapital or str(nueva_calificacion.SecuenciaEvento) if nueva_calificacion.SecuenciaEvento else '',
                        'fecha_pago': nueva_calificacion.FechaPago.strftime('%Y-%m-%d') if nueva_calificacion.FechaPago else '',
                        'secuencia': nueva_calificacion.SecuenciaEvento or '',
                        'anho': nueva_calificacion.Anho or nueva_calificacion.Ejercicio or '',
                        'valor_historico': str(nueva_calificacion.ValorHistorico or 0.0),
                        'descripcion': nueva_calificacion.Descripcion or ''
                    }
                })
        else:
            # Si el formulario no es válido, retornar errores en JSON
            # form.errors.as_json() convierte los errores de Django a formato JSON
            return JsonResponse({'success': False, 'error': form.errors.as_json()}, status=400)
    else:
        # Si es método GET, mostrar formulario
        # Puede recibir datos iniciales desde la URL para prellenar el formulario
        initial_data = {
            'Mercado': request.GET.get('mercado'),
            'Ejercicio': request.GET.get('ejercicio'),
            'Instrumento': request.GET.get('instrumento'),
            'FechaPago': request.GET.get('fecha_pago'),
            'SecuenciaEvento': request.GET.get('secuencia'),
        }
        
        # Crear formulario con datos iniciales (si los hay)
        form = CalificacionModalForm(initial=initial_data)

    # Renderizar template con el formulario
    return render(request, 'prueba/ingresar.html', {'form': form})


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
                # Importar Decimal para cálculos financieros precisos
                from decimal import Decimal
                
                # OBTENER TODOS LOS MONTOS DEL FORMULARIO
                # Convertir todos los montos a Decimal para precisión
                montos = {}
                for i in range(8, 38):  # Del 8 al 37 (30 montos)
                    monto_key = f'monto_{i}'  # Nombre del campo en el formulario
                    monto_value = form.cleaned_data.get(monto_key, Decimal(0))
                    
                    # Convertir a Decimal si no lo es
                    # POR QUÉ: Asegurar que todos los montos sean Decimal para cálculos precisos
                    if not isinstance(monto_value, Decimal):
                        montos[i] = Decimal(str(monto_value)) if monto_value else Decimal(0)
                    else:
                        montos[i] = monto_value
                
                # CALCULAR LA SUMA BASE
                # Suma de montos del 8 al 19 (inclusive)
                # POR QUÉ: La SumaBase es el denominador para calcular factores
                suma_base = Decimal(0)
                for i in range(8, 20):  # Del 8 al 19 inclusive
                    suma_base += montos.get(i, Decimal(0))
                
                # CREAR NUEVA CALIFICACIÓN
                nueva_calificacion = Calificacion()
                
                # Asignar datos generales del formulario
                nueva_calificacion.Ejercicio = form.cleaned_data.get('Ejercicio')
                
                # NORMALIZAR MERCADO
                mercado_raw = form.cleaned_data.get('Mercado', '')
                mercado_normalizado = mercado_raw
                if mercado_raw:
                    mercado_lower = mercado_raw.lower().strip()
                    if mercado_lower == 'acciones' or mercado_lower == 'accion':
                        mercado_normalizado = 'acciones'
                    elif mercado_lower == 'cfi':
                        mercado_normalizado = 'CFI'
                    elif mercado_lower == 'fondos mutuos' or mercado_lower == 'fondosmutuos' or mercado_lower == 'fondo mutuo':
                        mercado_normalizado = 'Fondos mutuos'
                
                nueva_calificacion.Mercado = mercado_normalizado
                nueva_calificacion.Instrumento = form.cleaned_data.get('Instrumento', '')
                
                # NORMALIZAR ORIGEN
                origen_raw = form.cleaned_data.get('Origen', 'corredor')
                origen_normalizado = origen_raw
                if origen_raw:
                    origen_lower = origen_raw.lower().strip()
                    if origen_lower == 'csv':
                        origen_normalizado = 'csv'
                    elif origen_lower == 'corredor' or origen_lower == 'manual':
                        origen_normalizado = 'corredor'
                
                nueva_calificacion.Origen = origen_normalizado
                
                # CALCULAR TODOS LOS FACTORES
                # Fórmula: Factor = Monto / SumaBase
                # Precisión: 8 decimales (requisito de negocio)
                EIGHT_PLACES = Decimal('0.00000001')
                
                if suma_base > 0:
                    # Calcular todos los factores del 8 al 37
                    for i in range(8, 38):
                        factor_field = f'Factor{i:02d}'
                        monto = montos.get(i, Decimal(0))
                        # Calcular factor: Monto / SumaBase
                        # .quantize() redondea a 8 decimales
                        factor_calculado = (monto / suma_base).quantize(EIGHT_PLACES)
                        setattr(nueva_calificacion, factor_field, factor_calculado)
                else:
                    # Si SumaBase es 0, todos los factores son 0
                    # POR QUÉ: Evitar división por cero
                    for i in range(8, 38):
                        factor_field = f'Factor{i:02d}'
                        setattr(nueva_calificacion, factor_field, Decimal(0))
                
                # Guardar la calificación con factores calculados
                nueva_calificacion.save()
                
                # Crear log de auditoría
                _crear_log(
                    current_user,
                    'Crear Calificacion',
                    documento_afectado=nueva_calificacion
                )
                
                # Mostrar mensaje de éxito y redirigir
                messages.success(request, '¡Calificación ingresada y calculada con éxito!')
                return redirect('home')
                
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
    Vista para guardar los factores calculados en la calificación.
    
    POR QUÉ ESTA FUNCIÓN ES NECESARIA:
    - Guarda los factores que el usuario calculó y revisó
    - Es la segunda parte del flujo: primero se calculan factores, luego se guardan
    - Solo guarda factores, no modifica montos (los montos ya se guardaron antes)
    - Registra cambios para auditoría
    
    CÓMO FUNCIONA:
    1. Usuario calcula factores con calcular_factores_view()
    2. Usuario revisa los factores en la interfaz
    3. Usuario confirma y llama esta función
    4. Sistema guarda solo los factores que cambiaron
    5. Actualiza FechaAct y crea log de auditoría
    
    FLUJO COMPLETO:
    1. calcular_factores_view() calcula y muestra factores (no guarda)
    2. Usuario revisa factores
    3. guardar_factores_view() guarda los factores confirmados
    
    Argumentos:
        request: Objeto HttpRequest de Django
        
    Returns (lo que devuelve la funcion):
        JsonResponse: JSON con el resultado de la operación
    """
    # Verificar autenticación del usuario
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    # Obtener usuario actual
    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401)

    # Obtener ID de la calificación desde el POST
    calificacion_id = request.POST.get('calificacion_id')
    if not calificacion_id:
        return JsonResponse({'success': False, 'error': 'Falta calificacion_id'}, status=400)

    # Obtener la calificación de MongoDB
    try:
        calificacion = Calificacion.objects.get(id=calificacion_id)
    except Calificacion.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Calificación no encontrada'}, status=404)

    try:
        # Importar Decimal para precisión financiera
        from decimal import Decimal
        
        # IMPORTANTE: Los montos ya fueron guardados cuando se calcularon los factores
        # calcular_factores_view() guarda los montos antes de calcular factores
        # Esta función solo guarda los factores, no modifica montos
        
        # Inicializar lista para registrar cambios
        cambios_detallados = []
        
        # Flag para saber si hubo cambios reales
        factores_actualizados = False
        
        # Iterar sobre todos los factores del 8 al 37
        for i in range(8, 38):
            # Construir nombre del campo: "Factor08", "Factor09", etc.
            factor_field = f'Factor{i:02d}'
            
            # Obtener valor del factor desde el POST
            valor_post = request.POST.get(factor_field)
            
            # Solo procesar si el valor fue enviado (no None)
            # POR QUÉ: Algunos factores pueden no estar en el POST
            if valor_post is not None:
                try:
                    # Convertir string a Decimal
                    # Decimal(str(valor)) es más seguro que Decimal(float(valor))
                    valor_decimal = Decimal(str(valor_post)) if valor_post else Decimal(0)
                    
                    # Obtener valor actual del factor en la calificación
                    valor_actual = getattr(calificacion, factor_field, Decimal(0))
                    
                    # Solo actualizar si el nuevo valor es diferente del actual
                    # POR QUÉ: Evitamos actualizaciones innecesarias
                    if valor_decimal != valor_actual:
                        # Registrar el cambio para el log de auditoría
                        cambios_detallados.append({
                            'campo': factor_field,
                            'valor_anterior': str(valor_actual),
                            'valor_nuevo': str(valor_decimal)
                        })
                        
                        # Actualizar el factor en el objeto calificación
                        setattr(calificacion, factor_field, valor_decimal)
                        
                        # Marcar que hubo cambios
                        factores_actualizados = True
                except (ValueError, TypeError):
                    # Si el valor no es un número válido, mantener el valor actual
                    # POR QUÉ: Mejor mantener valor actual que usar 0 incorrecto
                    pass
        
        # GUARDAR CAMBIOS EN MONGODB
        # Solo actualizar FechaAct si realmente hubo cambios
        if factores_actualizados:
            # Actualizar fecha de última modificación
            calificacion.FechaAct = datetime.datetime.now()
            
            # Guardar los cambios en MongoDB
            calificacion.save()
            
            # Crear log de auditoría con los cambios detallados
            _crear_log(current_user, 'Modificar Calificacion', documento_afectado=calificacion, cambios_detallados=cambios_detallados if cambios_detallados else None)
        else:
            # Si no hubo cambios, crear log sin cambios detallados
            # POR QUÉ: Aún así registramos que se intentó guardar
            _crear_log(current_user, 'Modificar Calificacion', documento_afectado=calificacion)
        
        # Retornar éxito
        return JsonResponse({'success': True})
    except Exception as e:
        # Si ocurre cualquier error, capturarlo y retornar error
        print(f"Error al guardar factores: {e}")
        return JsonResponse({'success': False, 'error': f'Error al guardar: {str(e)}'}, status=500)


# =====================================================================
# VISTAS DE FACTORES Y MONTOS (CÁLCULOS)
# =====================================================================

@require_POST
def calcular_factores_view(request):
    """
    Vista AJAX para calcular factores desde MONTOS ingresados.
    
    POR QUÉ ESTA FUNCIÓN ES CRÍTICA:
    - Es el corazón del cálculo financiero del sistema
    - Calcula factores a partir de montos (dinero)
    - Los factores representan porcentajes de participación
    - Se usa Decimal para precisión financiera (evita errores de punto flotante)
    
    FÓRMULA PRINCIPAL:
    - SumaBase = suma de montos del 8 al 19
    - Factor = Monto / SumaBase (para cada monto del 8 al 37)
    - Los factores siempre están entre 0 y 1 (representan porcentajes)
    
    CÓMO FUNCIONA:
    1. Usuario ingresa montos en el formulario
    2. Sistema calcula SumaBase (suma de montos 8-19)
    3. Para cada monto (8-37), calcula Factor = Monto / SumaBase
    4. Guarda los montos en la calificación
    5. Retorna factores calculados para mostrar al usuario (sin guardar aún)
    6. Usuario puede revisar y luego confirmar para guardar
    
    El usuario ingresa montos, y esta vista calcula los factores:
    - SumaBase = suma de montos del 8 al 19
    - Factor = Monto / SumaBase para cada monto del 8 al 37
    
    No guarda los factores, solo los calcula y los retorna para previsualización.
    
    Argumentos:
        request: Objeto HttpRequest de Django (solo POST permitido)
        
    Returns (lo que devuelve la funcion):
        JsonResponse: JSON con factores calculados para mostrar al usuario
    """
    # Verificar autenticación del usuario
    # POR QUÉ: Solo usuarios autenticados pueden calcular factores
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    # Obtener usuario actual de la base de datos
    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
    except usuarios.DoesNotExist:
        # Si el usuario no existe, la sesión es inválida
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401)

    # Obtener ID de la calificación desde el POST
    # POR QUÉ: Necesitamos saber qué calificación estamos modificando
    calificacion_id = request.POST.get('calificacion_id')
    if not calificacion_id:
        return JsonResponse({'success': False, 'error': 'Falta calificacion_id'}, status=400)

    # Obtener la calificación de MongoDB
    try:
        calificacion = Calificacion.objects.get(id=calificacion_id)
    except Calificacion.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Calificación no encontrada'}, status=404)

    try:
        # Importar Decimal para cálculos financieros precisos
        # POR QUÉ: float tiene errores de precisión (0.1 + 0.2 = 0.30000000000000004)
        # Decimal mantiene precisión exacta para cálculos financieros
        from decimal import Decimal
        
        # OBTENER MONTOS DEL FORMULARIO
        # El usuario ingresa montos en campos: monto_8, monto_9, ..., monto_37
        montos = {}  # Diccionario: {8: Decimal(1000), 9: Decimal(500), ...}
        
        # Iterar sobre todos los montos del 8 al 37 (30 montos totales)
        for i in range(8, 38):
            # Construir nombre del campo: "monto_8", "monto_9", etc.
            monto_key = f'monto_{i}'
            
            # Obtener valor del POST, usar '0.00' como valor por defecto si no existe
            valor_post = request.POST.get(monto_key, '0.00')
            
            try:
                # Convertir string a Decimal
                # Decimal(str(valor)) es más seguro que Decimal(float(valor))
                # POR QUÉ: float puede introducir errores de precisión
                # Si valor_post está vacío o es None, usar Decimal(0)
                montos[i] = Decimal(str(valor_post)) if valor_post else Decimal(0)
            except (ValueError, TypeError):
                # Si el valor no es un número válido, usar 0
                # POR QUÉ: Mejor usar 0 que fallar la operación completa
                montos[i] = Decimal(0)

        # CALCULAR SUMA BASE
        # SumaBase = suma de montos del 8 al 19 (12 montos)
        # POR QUÉ: Los factores se calculan dividiendo cada monto por esta suma
        # Esta es la base de referencia para todos los cálculos
        suma_base = Decimal(0)
        
        # Iterar del 8 al 19 (inclusive)
        # range(8, 20) genera: 8, 9, 10, ..., 19
        for i in range(8, 20):
            # Sumar cada monto a la suma base
            # .get(i, Decimal(0)) obtiene el monto o 0 si no existe
            suma_base += montos.get(i, Decimal(0))

        # GUARDAR MONTOS EN LA CALIFICACIÓN
        # Solo guardamos los montos que fueron enviados y son diferentes del valor actual
        # POR QUÉ: Si un monto no se envía o es 0, mantenemos el valor actual en la base de datos
        # Esto permite actualizar solo algunos montos sin perder los demás
        
        # Lista para registrar todos los cambios realizados (para el log de auditoría)
        cambios_detallados = []
        
        # Flag para saber si se actualizó algún monto
        # POR QUÉ: Solo actualizamos FechaAct si realmente hubo cambios
        montos_actualizados = False
        
        # Iterar sobre todos los montos del 8 al 37
        for i in range(8, 38):
            # Construir nombre del campo en el modelo: "Monto08", "Monto09", etc.
            # :02d formatea el número con 2 dígitos y ceros a la izquierda (8 -> "08")
            monto_field = f'Monto{i:02d}'
            
            # Obtener el valor del monto del diccionario montos
            monto_value = montos.get(i, Decimal(0))
            
            # Obtener el valor actual del monto en la calificación
            # getattr() obtiene el atributo del objeto, o Decimal(0) si no existe
            valor_actual = getattr(calificacion, monto_field, Decimal(0))
            
            # Solo actualizar si el nuevo valor es diferente del actual
            # POR QUÉ: Evitamos actualizaciones innecesarias y registramos solo cambios reales
            if monto_value != valor_actual:
                # Registrar el cambio en la lista de cambios detallados
                # Esto se guardará en el log para auditoría
                cambios_detallados.append({
                    'campo': monto_field,  # Nombre del campo que cambió
                    'valor_anterior': str(valor_actual),  # Valor antes del cambio
                    'valor_nuevo': str(monto_value)  # Valor después del cambio
                })
                
                # Actualizar el campo en el objeto calificación
                # setattr() asigna un valor a un atributo del objeto dinámicamente
                setattr(calificacion, monto_field, monto_value)
                
                # Marcar que hubo cambios
                montos_actualizados = True
        
        # GUARDAR SUMA BASE EN LA CALIFICACIÓN
        # La SumaBase se guarda para poder hacer el cálculo inverso después
        # POR QUÉ: Si queremos recuperar los montos desde los factores, necesitamos la SumaBase
        # Fórmula inversa: Monto = Factor * SumaBase
        
        # Obtener la SumaBase actual de la calificación
        suma_base_actual = getattr(calificacion, 'SumaBase', Decimal(0))
        
        # Solo actualizar si la nueva SumaBase es diferente
        if suma_base != suma_base_actual:
            # Registrar el cambio de SumaBase
            cambios_detallados.append({
                'campo': 'SumaBase',
                'valor_anterior': str(suma_base_actual),
                'valor_nuevo': str(suma_base)
            })
            
            # Actualizar SumaBase en la calificación
            calificacion.SumaBase = suma_base
            montos_actualizados = True
        
        # ACTUALIZAR FECHA DE MODIFICACIÓN Y GUARDAR
        # Solo actualizamos si realmente hubo cambios en los montos
        # POR QUÉ: No queremos actualizar FechaAct si no hubo cambios reales
        if montos_actualizados:
            # Actualizar fecha de última modificación
            calificacion.FechaAct = datetime.datetime.now()
            
            # Guardar los cambios en MongoDB
            calificacion.save()
            
            # Crear log de auditoría con los cambios detallados
            # Si hay cambios, los incluimos; si no, pasamos None
            _crear_log(current_user, 'Modificar Calificacion', documento_afectado=calificacion, cambios_detallados=cambios_detallados if cambios_detallados else None)
        
        # CALCULAR FACTORES
        # Fórmula: Factor = Monto / SumaBase para cada monto del 8 al 37
        # Los factores representan el porcentaje que representa cada monto respecto a la SumaBase
        
        # Precisión de 8 decimales para los factores
        # Decimal('0.00000001') representa 0.00000001 (8 decimales)
        # POR QUÉ: Los cálculos financieros requieren alta precisión
        EIGHT_PLACES = Decimal('0.00000001')
        
        # Diccionario para almacenar los factores calculados
        factores_calculados = {}
        
        # Solo calcular factores si SumaBase es mayor que 0
        # POR QUÉ: No podemos dividir por cero
        if suma_base > 0:
            # Iterar sobre todos los montos del 8 al 37
            for i in range(8, 38):
                # Obtener el monto correspondiente
                monto = montos.get(i, Decimal(0))
                
                # Calcular el factor: Monto dividido por SumaBase
                # quantize() redondea el resultado a 8 decimales
                # POR QUÉ: Mantenemos precisión consistente en todos los factores
                factor_calculado = (monto / suma_base).quantize(EIGHT_PLACES)
                
                # Construir nombre del campo: "Factor08", "Factor09", etc.
                factor_field = f'Factor{i:02d}'
                
                # Guardar el factor calculado como string en el diccionario
                # Convertimos a string para facilitar el envío en JSON
                factores_calculados[factor_field] = str(factor_calculado)
        else:
            # Si SumaBase es 0, todos los factores son 0
            # POR QUÉ: No hay base para calcular porcentajes
            for i in range(8, 38):
                factor_field = f'Factor{i:02d}'
                factores_calculados[factor_field] = '0.00000000'

        # FORMATEAR FACTORES PARA MOSTRAR AL USUARIO
        # Los factores se formatean para eliminar ceros innecesarios
        # POR QUÉ: "0.25000000" se muestra mejor como "0.25" para el usuario
        # No guardamos aún, solo previsualizamos para que el usuario revise antes de confirmar
        
        factores_formateados = {}
        
        # Iterar sobre todos los factores del 8 al 37
        for i in range(8, 38):
            factor_field = f'Factor{i:02d}'
            
            # Obtener el valor del factor calculado, usar '0.00000000' si no existe
            valor_str = factores_calculados.get(factor_field, '0.00000000')
            
            # Formatear el valor eliminando ceros innecesarios
            try:
                # Convertir string a float para formatear
                valor_float = float(valor_str)
                
                # Formatear a 8 decimales y eliminar ceros innecesarios
                # f"{valor_float:.8f}" formatea a 8 decimales: 0.25 -> "0.25000000"
                # .rstrip('0') elimina ceros a la derecha: "0.25000000" -> "0.25"
                # .rstrip('.') elimina el punto si no hay decimales: "1." -> "1"
                factor_formateado = f"{valor_float:.8f}".rstrip('0').rstrip('.')
                
                # Si después de eliminar ceros queda string vacío, es porque el valor es 0
                if factor_formateado == '':
                    factor_formateado = '0'
                
                factores_formateados[factor_field] = factor_formateado
            except (ValueError, TypeError):
                # Si hay error al convertir, usar '0.0' como valor por defecto
                factores_formateados[factor_field] = '0.0'

        # CREAR INFORMACIÓN DE DEBUG
        # Esta información ayuda a diagnosticar problemas durante desarrollo
        # POR QUÉ: Permite ver los valores intermedios y comparar resultados
        # NO incluir debug_info dentro de sí mismo para evitar referencia circular
        debug_info = {
            'suma_base': str(suma_base),
            'factores_calculados': factores_calculados,
            'factores_formateados': factores_formateados
        }

        # RETORNAR RESPUESTA JSON
        # La respuesta incluye los factores formateados para mostrar al usuario
        # También incluye información de debug para desarrollo
        return JsonResponse({
            'success': True,  # Indica que la operación fue exitosa
            'message': 'Factores calculados exitosamente',  # Mensaje de confirmación
            'factores': factores_formateados,  # Factores listos para mostrar en la interfaz
            'suma_base': str(suma_base),  # Suma base calculada
            'debug': debug_info  # Información adicional para debugging
        })

    except Exception as e:
        # Si ocurre cualquier error durante el cálculo, capturarlo y retornar error
        # POR QUÉ: Mejor retornar un error claro que dejar que la excepción se propague
        print(f"Error al calcular factores: {e}")
        return JsonResponse({'success': False, 'error': f'Error al calcular: {str(e)}'}, status=500)


# =====================================================================
# VISTAS DE ADMINISTRACIÓN DE USUARIOS
# =====================================================================

def administrar_view(request): 
    """
    Vista para administrar usuarios (solo administradores).
    
    POR QUÉ ESTA FUNCIÓN ES IMPORTANTE:
    - Permite a los administradores gestionar usuarios del sistema
    - Muestra lista completa de usuarios para administración
    - Controla acceso solo para administradores (seguridad)
    - Es el punto de entrada para crear, modificar y eliminar usuarios
    
    CÓMO FUNCIONA:
    1. Verifica que el usuario esté autenticado
    2. Verifica que el usuario sea administrador
    3. Obtiene todos los usuarios de la base de datos
    4. Renderiza template con la lista de usuarios
    
    Muestra la lista de todos los usuarios del sistema.
    Permite crear, modificar y eliminar usuarios.
    
    Argumentos:
        request: Objeto HttpRequest de Django
        
    Returns (lo que devuelve la funcion):
        HttpResponseForbidden: Si el usuario no es administrador
        HttpResponse: Renderiza administrar.html con la lista de usuarios
    """
    # Verificar autenticación del usuario
    if 'user_id' not in request.session:
        return redirect('login')

    # Obtener usuario actual de la base de datos
    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
    except usuarios.DoesNotExist:
        # Si el usuario no existe, limpiar sesión y redirigir
        request.session.flush()
        return redirect('login')

    # Verificar que el usuario sea administrador
    # current_user.rol es True para administradores, False para usuarios normales
    # POR QUÉ: Solo administradores pueden acceder a esta página
    if not current_user.rol:
        return HttpResponseForbidden("<h1>Acceso Denegado</h1><p>No tienes permisos...</p><a href='/home/'>Volver</a>")
    
    # Obtener todos los usuarios del sistema
    # usuarios.objects.all() consulta la colección 'usuarios' y retorna todos los documentos
    todos_los_usuarios = usuarios.objects.all()
    
    # Renderizar template con la lista de usuarios
    # El template mostrará la lista y permitirá crear, modificar y eliminar usuarios
    return render(request, 'prueba/administrar.html', {
        'user_nombre': current_user.nombre,  # Nombre del usuario actual (para mostrar en la interfaz)
        'lista_usuarios': todos_los_usuarios,  # Lista de todos los usuarios (para mostrar en tabla)
        'is_admin': current_user.rol,  # Indica si es admin (para mostrar opciones adicionales)
        'current_user_id': str(current_user.id)  # ID del usuario actual (para evitar auto-eliminación)
    })


# =====================================================================
# VISTAS DE CREAR USUARIO
# =====================================================================

@require_POST
def crear_usuario_view(request):
    """
    Vista AJAX para crear un nuevo usuario (solo administradores).
    
    POR QUÉ ESTA FUNCIÓN ES IMPORTANTE:
    - Permite a administradores crear nuevos usuarios del sistema
    - Valida datos antes de guardar (seguridad)
    - Hashea contraseñas antes de guardar (nunca en texto plano)
    - Maneja fotos de perfil opcionales
    - Registra la acción en logs de auditoría
    
    CÓMO FUNCIONA:
    1. Verifica que el usuario sea administrador
    2. Valida el formulario con Django
    3. Hashea la contraseña con bcrypt
    4. Crea el usuario en MongoDB
    5. Si hay foto, la guarda y redimensiona
    6. Crea log de auditoría
    7. Retorna éxito o error en JSON
    
    Valida el formulario, hashea la contraseña y guarda el usuario en MongoDB.
    También maneja la foto de perfil si se proporciona.
    
    Argumentos:
        request: Objeto HttpRequest de Django (solo POST permitido)
        
    Returns (lo que devuelve la funcion):
        JsonResponse: JSON con success=True si se creó exitosamente, o errores si falló
    """
    # Verificar autenticación del usuario
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    # Verificar que el usuario sea administrador
    try:
        admin_user = usuarios.objects.get(id=request.session['user_id'])
        if not admin_user.rol:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Admin no válido'}, status=401)

    # Crear formulario con datos del POST
    form = UsuarioForm(request.POST)
    
    # Validar formulario
    if form.is_valid():
        try:
            # Copiar datos limpios del formulario
            cleaned_data = form.cleaned_data.copy()
            
            # Eliminar campo confirmar_contrasena
            # POR QUÉ: Este campo solo se usa para validar que las contraseñas coincidan
            # No se guarda en la base de datos
            cleaned_data.pop('confirmar_contrasena', None)
            
            # Hashear la contraseña antes de guardar
            # POR QUÉ: NUNCA guardamos contraseñas en texto plano (seguridad crítica)
            if 'contrasena' in cleaned_data and cleaned_data['contrasena']:
                cleaned_data['contrasena'] = _hash_password(cleaned_data['contrasena'])
            
            # Crear nuevo usuario con los datos del formulario
            # **cleaned_data expande el diccionario como argumentos
            nuevo_usuario = usuarios(**cleaned_data)
            
            # Guardar primero para obtener el ID
            # POR QUÉ: Necesitamos el ID para nombrar la foto de perfil de forma única
            nuevo_usuario.save()
            
            # MANEJAR FOTO DE PERFIL (OPCIONAL)
            # Si el usuario subió una foto, guardarla y redimensionarla
            if 'foto_perfil' in request.FILES:
                try:
                    # Guardar foto de perfil
                    # _guardar_foto_perfil() valida, redimensiona y guarda la imagen
                    foto_ruta = _guardar_foto_perfil(request.FILES['foto_perfil'], str(nuevo_usuario.id))
                    
                    # Asignar ruta de la foto al usuario
                    nuevo_usuario.foto_perfil = foto_ruta
                    
                    # Guardar nuevamente con la ruta de la foto
                    nuevo_usuario.save()
                except ValueError as e:
                    # Si la foto es inválida (tamaño, formato), eliminar usuario y retornar error
                    # POR QUÉ: No queremos usuarios sin foto válida en la base de datos
                    nuevo_usuario.delete()
                    return JsonResponse({'success': False, 'error': str(e)}, status=400)
                except Exception as e:
                    # Si hay otro error al guardar la foto, eliminar usuario
                    nuevo_usuario.delete()
                    print(f"Error al guardar foto: {e}")
                    return JsonResponse({'success': False, 'error': f'Error al guardar foto: {e}'}, status=500)
            
            # Crear log de auditoría
            # Registra quién creó el usuario y qué usuario se creó
            _crear_log(admin_user, "Crear Usuario", usuario_afectado=nuevo_usuario)
            
            # Retornar éxito
            return JsonResponse({'success': True, 'message': 'Usuario creado exitosamente'})
        except Exception as e:
            # Si ocurre cualquier error durante la creación, capturarlo
            print(f"Error al crear usuario: {e}")
            return JsonResponse({'success': False, 'error': f'Error interno: {e}'}, status=500)
    else:
        # Si el formulario no es válido, extraer el primer error
        # POR QUÉ: Mostrar un error claro al usuario en lugar de todos los errores
        error_mensaje = "Error de validación: "
        if form.errors:
            # Obtener el primer campo con error
            primer_campo = list(form.errors.keys())[0]
            # Obtener el primer error de ese campo
            primer_error = form.errors[primer_campo][0]
            error_mensaje = str(primer_error)
        return JsonResponse({'success': False, 'error': error_mensaje}, status=400)


# =====================================================================
# VISTAS DE ELIMINAR USUARIOS
# =====================================================================

@require_POST
def eliminar_usuarios_view(request):
    """
    Vista AJAX para eliminar usuarios (solo administradores).
    
    POR QUÉ ESTA FUNCIÓN ES IMPORTANTE:
    - Permite a administradores eliminar usuarios del sistema
    - Previene auto-eliminación (seguridad)
    - Elimina fotos de perfil asociadas (limpieza)
    - Permite eliminar múltiples usuarios a la vez
    - Registra todas las eliminaciones en logs de auditoría
    
    CÓMO FUNCIONA:
    1. Verifica que el usuario sea administrador
    2. Recibe lista de IDs de usuarios a eliminar (JSON)
    3. Previene auto-eliminación
    4. Para cada usuario: elimina foto de perfil y crea log
    5. Elimina usuarios de MongoDB
    6. Retorna cantidad de usuarios eliminados
    
    Elimina usuarios de la base de datos.
    
    Argumentos:
        request: Objeto HttpRequest de Django (solo POST permitido)
        
    Returns (lo que devuelve la funcion):
        JsonResponse: JSON con success=True si se eliminó exitosamente, o errores si falló
    """
    # Verificar autenticación del usuario
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    # Verificar que el usuario sea administrador
    try:
        admin_user = usuarios.objects.get(id=request.session['user_id'])
        if not admin_user.rol:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Admin no válido'}, status=401)

    # PARSEAR JSON DEL BODY
    # Los IDs vienen en formato JSON en el body de la petición
    try:
        # json.loads() convierte string JSON a diccionario Python
        data = json.loads(request.body)
        
        # Obtener lista de IDs de usuarios a eliminar
        # user_ids es una lista de strings: ["id1", "id2", "id3"]
        user_ids_to_delete_str = data.get('user_ids', [])
        
        # Validar que sea una lista no vacía
        if not isinstance(user_ids_to_delete_str, list) or not user_ids_to_delete_str:
            return JsonResponse({'success': False, 'error': 'Lista de IDs inválida'}, status=400)
    except json.JSONDecodeError:
        # Si el JSON es inválido, retornar error
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

    # PREVENIR AUTO-ELIMINACIÓN
    # Un administrador no puede eliminarse a sí mismo
    # POR QUÉ: Seguridad - evitar que un admin se bloquee a sí mismo del sistema
    if request.session['user_id'] in user_ids_to_delete_str:
        return JsonResponse({'success': False, 'error': 'No puedes eliminarte a ti mismo'}, status=400)

    # CONVERTIR STRINGS A OBJECTIDS
    # MongoDB requiere ObjectId, no strings
    try:
        # Convertir cada string ID a ObjectId
        # ObjectId() valida el formato (24 caracteres hexadecimales)
        ids_a_eliminar = [ObjectId(uid) for uid in user_ids_to_delete_str]
    except Exception:
        # Si algún ID tiene formato inválido, retornar error
        return JsonResponse({'success': False, 'error': 'Uno o más IDs tienen un formato inválido'}, status=400)

    # PROCESAR CADA USUARIO A ELIMINAR
    # Antes de eliminar, necesitamos obtener información para el log y eliminar la foto
    for user_id in ids_a_eliminar:
        try:
            # Obtener el usuario antes de eliminarlo
            # POR QUÉ: Necesitamos su información para el log y para eliminar la foto
            usuario_eliminado = usuarios.objects.get(id=user_id)
            
            # ELIMINAR FOTO DE PERFIL SI EXISTE
            # Limpiar archivos del sistema de archivos
            if usuario_eliminado.foto_perfil:
                try:
                    # Construir ruta completa del archivo
                    foto_path = settings.MEDIA_ROOT / usuario_eliminado.foto_perfil
                    
                    # Verificar que el archivo existe antes de eliminarlo
                    if foto_path.exists():
                        # Eliminar archivo del disco
                        foto_path.unlink()
                        print(f"Foto de perfil eliminada: {foto_path}")
                except Exception as e:
                    # Si falla la eliminación de la foto, solo imprimir error
                    # POR QUÉ: No queremos que un error al eliminar foto impida eliminar el usuario
                    print(f"Error al eliminar foto de perfil: {e}")
            
            # Crear log de auditoría antes de eliminar
            # POR QUÉ: Necesitamos la información del usuario para el log
            _crear_log(
                admin_user,  # Usuario que ejecutó la eliminación
                'Eliminar Usuario',  # Acción realizada
                usuario_afectado=usuario_eliminado  # Usuario que fue eliminado
            )
        except usuarios.DoesNotExist:
            # Si el usuario ya no existe, crear log solo con el ID
            # POR QUÉ: Puede haber sido eliminado entre la validación y la eliminación
            _crear_log(
                admin_user,
                'Eliminar Usuario',
                usuario_afectado=user_id
            )
    
    # ELIMINAR USUARIOS DE MONGODB
    # id__in busca documentos cuyo ID esté en la lista
    # delete() elimina todos los documentos que coinciden
    # Retorna la cantidad de documentos eliminados
    delete_result = usuarios.objects(id__in=ids_a_eliminar).delete()

    # Retornar éxito con la cantidad de usuarios eliminados
    return JsonResponse({'success': True, 'deleted_count': delete_result})


# =====================================================================
# VISTAS DE OBTENER USUARIO
# =====================================================================
@require_GET
def obtener_usuario_view(request, user_id): 
    """
    Vista AJAX para obtener un usuario (solo administradores).
    
    POR QUÉ ESTA FUNCIÓN ES NECESARIA:
    - Permite obtener datos de un usuario para editarlo
    - JavaScript llama esta función para prellenar el formulario de edición
    - Solo administradores pueden ver datos de otros usuarios
    - Retorna datos en formato JSON para uso dinámico
    
    CÓMO FUNCIONA:
    1. Verifica que el usuario sea administrador
    2. Busca el usuario por ID en MongoDB
    3. Serializa los datos a diccionario
    4. Retorna JSON con los datos del usuario
    
    Obtiene un usuario de la base de datos.
    
    Argumentos:
        request: Objeto HttpRequest de Django (solo GET permitido)
        user_id: ID del usuario a obtener
    """
    # Verificar autenticación del usuario
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    # Verificar que el usuario sea administrador
    try:
        admin_user = usuarios.objects.get(id=request.session['user_id'])
        if not admin_user.rol:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Admin no válido'}, status=401)

    # Obtener usuario de la base de datos
    try:
        usuario = usuarios.objects.get(id=user_id)
        
        # Crear diccionario con datos del usuario
        # Convertir ObjectId a string para JSON
        # or None convierte string vacío a None para consistencia
        usuario_data = {
            'id': str(usuario.id),  # ID como string
            'nombre': usuario.nombre,  # Nombre completo
            'correo': usuario.correo,  # Correo electrónico
            'rol': usuario.rol,  # True si es admin, False si es usuario normal
            'foto_perfil': usuario.foto_perfil if usuario.foto_perfil else None  # Ruta de foto o None
        }
        
        # Retornar JSON con los datos del usuario
        return JsonResponse({'success': True, 'usuario': usuario_data})
    except usuarios.DoesNotExist:
        # Si el usuario no existe, retornar error
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        # Si ocurre cualquier otro error, capturarlo
        return JsonResponse({'success': False, 'error': f'Error interno: {e}'}, status=500)


# =====================================================================
# VISTAS DE MODIFICAR USUARIO
# =====================================================================
@require_POST
def modificar_usuario_view(request):
    """
    Vista AJAX para modificar un usuario (solo administradores).
    
    POR QUÉ ESTA FUNCIÓN ES IMPORTANTE:
    - Permite a administradores actualizar datos de usuarios
    - Valida datos antes de guardar (seguridad)
    - Hashea contraseñas solo si se proporcionan (opcional)
    - Maneja actualización de fotos de perfil (elimina foto antigua)
    - Registra cambios en logs de auditoría
    
    CÓMO FUNCIONA:
    1. Verifica que el usuario sea administrador
    2. Valida el formulario
    3. Obtiene datos del formulario
    4. Busca el usuario a modificar
    5. Actualiza campos (nombre, correo, rol)
    6. Si hay nueva contraseña, la hashea y actualiza
    7. Si hay nueva foto, elimina la antigua y guarda la nueva
    8. Guarda cambios y crea log
    
    Modifica un usuario de la base de datos.
    """
    # Verificar autenticación del usuario
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    # Verificar que el usuario sea administrador
    try:
        admin_user = usuarios.objects.get(id=request.session['user_id'])
        if not admin_user.rol:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Admin no válido'}, status=401)

    # VALIDAR FORMULARIO
    # UsuarioUpdateForm valida nombre, correo, contraseña, rol, foto
    # request.FILES contiene archivos subidos (foto de perfil)
    form = UsuarioUpdateForm(request.POST, request.FILES)
    
    if not form.is_valid():
        # Si el formulario no es válido, retornar todos los errores
        errors_dict = {}
        for field, errors in form.errors.items():
            errors_dict[field] = errors
        return JsonResponse({'success': False, 'error': errors_dict}, status=400)
    
    # Obtener datos del formulario validado
    user_id = form.cleaned_data.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Falta user_id'}, status=400)

    # Extraer datos del formulario
    nombre = form.cleaned_data.get('nombre', '').strip()
    correo = form.cleaned_data.get('correo', '').strip()
    contrasena = form.cleaned_data.get('contrasena', '')  # Puede estar vacía
    rol = form.cleaned_data.get('rol', False)

    # Validar campos obligatorios
    if not nombre or not correo:
        return JsonResponse({'success': False, 'error': 'Nombre y correo son obligatorios.'}, status=400)

    try:
        # Obtener el usuario a modificar de MongoDB
        usuario_a_modificar = usuarios.objects.get(id=user_id)
        
        # ACTUALIZAR CAMPOS BÁSICOS
        usuario_a_modificar.nombre = nombre
        usuario_a_modificar.correo = correo
        
        # ACTUALIZAR CONTRASEÑA (SOLO SI SE PROPORCIONA)
        # Si la contraseña está vacía, no se actualiza (mantiene la actual)
        # POR QUÉ: Permite modificar otros campos sin cambiar la contraseña
        if contrasena and contrasena.strip():
            # Hashear la nueva contraseña antes de guardar
            # POR QUÉ: NUNCA guardamos contraseñas en texto plano
            usuario_a_modificar.contrasena = _hash_password(contrasena)
        
        # Actualizar rol
        usuario_a_modificar.rol = rol
        
        # MANEJAR FOTO DE PERFIL (OPCIONAL)
        # Si el usuario subió una nueva foto, reemplazar la antigua
        if 'foto_perfil' in request.FILES:
            try:
                # Eliminar foto anterior si existe
                # POR QUÉ: Evitar acumulación de archivos no utilizados
                if usuario_a_modificar.foto_perfil:
                    foto_antigua = settings.MEDIA_ROOT / usuario_a_modificar.foto_perfil
                    if foto_antigua.exists():
                        foto_antigua.unlink()
                
                # Guardar nueva foto de perfil
                # _guardar_foto_perfil() valida, redimensiona y guarda
                foto_ruta = _guardar_foto_perfil(request.FILES['foto_perfil'], str(usuario_a_modificar.id))
                usuario_a_modificar.foto_perfil = foto_ruta
            except ValueError as e:
                # Si la foto es inválida (tamaño, formato), retornar error
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
            except Exception as e:
                # Si hay otro error al guardar la foto
                print(f"Error al guardar foto: {e}")
                return JsonResponse({'success': False, 'error': f'Error al guardar foto: {e}'}, status=500)
        
        # Guardar todos los cambios en MongoDB
        usuario_a_modificar.save()
        
        # Crear log de auditoría
        # Registra quién modificó qué usuario
        _crear_log(admin_user, 'Modificar Usuario', usuario_afectado=usuario_a_modificar)
        
        return JsonResponse({'success': True})
    except usuarios.DoesNotExist:
        # Si el usuario no existe, retornar error
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        # Si ocurre cualquier otro error, capturarlo
        print("Error interno modificar_usuario_view:", e)
        return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'}, status=500)


# =====================================================================
# VISTAS DE LOGS Y AUDITORÍA
# =====================================================================

def ver_logs_view(request):
    """
    Vista para ver todos los logs del sistema (solo administradores).
    
    POR QUÉ ESTA FUNCIÓN ES CRÍTICA:
    - Proporciona auditoría completa del sistema
    - Permite rastrear quién hizo qué y cuándo
    - Esencial para seguridad y cumplimiento
    - Muestra acciones incluso si los usuarios/calificaciones fueron eliminados
    
    CÓMO FUNCIONA:
    1. Verifica que el usuario sea administrador
    2. Obtiene todos los logs de MongoDB (sin resolver referencias)
    3. Procesa cada log para extraer información de usuarios/calificaciones
    4. Maneja casos donde usuarios/calificaciones fueron eliminados
    5. Renderiza template con logs procesados
    
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
    # Verificar autenticación del usuario
    if 'user_id' not in request.session:
        return redirect('login')

    # Verificar que el usuario sea administrador
    try:
        admin_user = usuarios.objects.get(id=request.session['user_id'])
        if not admin_user.rol:
            return HttpResponseForbidden(
                "<h1>Acceso Denegado</h1>"
                "<p>No tienes permisos de administrador.</p>"
                "<a href='/home/'>Volver</a>"
            )
    except usuarios.DoesNotExist:
        # Si el usuario no existe, limpiar sesión y redirigir
        del request.session['user_id']
        del request.session['user_nombre']
        return redirect('login')

    try:
        # Obtener todos los logs de MongoDB
        # .no_dereference() evita resolver referencias automáticamente
        # POR QUÉ: Necesitamos los IDs incluso si los documentos fueron eliminados
        # .order_by('-fecharegistrada') ordena por fecha descendente (más recientes primero)
        logs_raw = Log.objects.no_dereference().order_by('-fecharegistrada')
        
        # Lista para almacenar logs procesados con información completa
        logs_procesados = []

        # PROCESAR CADA LOG
        # Extraer información de cada log para mostrar en la interfaz
        for l in logs_raw:
            # --- ACTOR (usuario que ejecutó la acción) ---
            # Obtener correo del actor (siempre está guardado en el log)
            actor_correo = getattr(l, "correoElectronico", "N/A")
            actor_id = "N/A"
            actor_nombre = "N/A"
            
            # Intentar obtener ID y nombre del actor
            # POR QUÉ: El actor puede haber sido eliminado, pero el log debe seguir mostrándose
            if hasattr(l, "Usuarioid") and l.Usuarioid:
                # Extraer ObjectId del actor
                actor_id_obj = _extraer_object_id(l.Usuarioid)
                if actor_id_obj:
                    actor_id = actor_id_obj
                    # Intentar obtener el nombre del actor si aún existe en la base de datos
                    try:
                        actor_usuario = usuarios.objects.get(id=actor_id_obj)
                        actor_nombre = actor_usuario.nombre
                    except usuarios.DoesNotExist:
                        # Si el usuario fue eliminado, mantener "N/A"
                        pass

            # --- ELEMENTO AFECTADO (usuario, calificación o carga masiva) ---
            # Determinar qué fue afectado por la acción
            afectado_id = "N/A"
            tipo_afectado = "N/A"  # Puede ser 'Usuario', 'Calificacion' o 'Carga-Masiva'
            
            # Verificar si es un usuario afectado
            if hasattr(l, "usuario_afectado") and l.usuario_afectado:
                afectado_id_obj = _extraer_object_id(l.usuario_afectado)
                if afectado_id_obj:
                    afectado_id = afectado_id_obj
                    tipo_afectado = "Usuario"
            # Verificar si es una calificación afectada
            elif hasattr(l, "iddocumento") and l.iddocumento:
                afectado_id_obj = _extraer_object_id(l.iddocumento)
                if afectado_id_obj:
                    afectado_id = afectado_id_obj
                    tipo_afectado = "Calificacion"
            # Verificar si es una carga masiva
            elif hasattr(l, "hash_archivo_csv") and l.hash_archivo_csv and getattr(l, "accion", "") == "Carga Masiva":
                # Para cargas masivas, usar el hash del archivo como identificador
                afectado_id = l.hash_archivo_csv
                tipo_afectado = "Carga-Masiva"
            
            # Agregar el log procesado a la lista
            logs_procesados.append({
                "fecha": getattr(l, "fecharegistrada", None),
                "actor_correo": actor_correo,
                "actor_id": actor_id,
                "actor_nombre": actor_nombre,
                "accion": getattr(l, "accion", "N/A"),
                "afectado_id": afectado_id,
                "tipo_afectado": tipo_afectado,
            })

    except Exception as e:
        # Si ocurre cualquier error al procesar logs, retornar error
        print(f"Error al cargar logs: {e}")
        return HttpResponseServerError(
            f"<h1>Error Interno</h1>"
            f"<p>No se pudieron cargar los logs del sistema.</p>"
            f"<p>Error: {e}</p>"
            f"<a href='/home/'>Volver</a>"
        )

    # Preparar contexto para el template
    context = {
        "user_nombre": admin_user.nombre,  # Nombre del administrador actual
        "lista_logs": logs_procesados,  # Lista de logs procesados
    }
    
    # Renderizar template con los logs
    return render(request, "prueba/ver_logs.html", context)


# =====================================================================
# VISTAS DE OBTENER CALIFICACIÓN
# =====================================================================
@require_GET
def obtener_calificacion_view(request, calificacion_id):
    """
    Vista AJAX para obtener una calificación por ID.
    
    POR QUÉ ESTA FUNCIÓN ES NECESARIA:
    - Permite obtener datos completos de una calificación para editarla
    - Calcula montos desde factores guardados (cálculo inverso)
    - JavaScript usa estos datos para prellenar formularios
    - Retorna tanto factores como montos calculados
    
    CÓMO FUNCIONA:
    1. Busca la calificación por ID en MongoDB
    2. Extrae todos los datos básicos de la calificación
    3. Obtiene factores guardados (Factor08 a Factor37)
    4. Calcula montos desde factores: Monto = Factor * SumaBase
    5. Retorna todo en formato JSON
    
    CÁLCULO INVERSO:
    - Si tenemos factores y SumaBase, podemos calcular montos
    - Fórmula: Monto = Factor * SumaBase
    - Esto permite reconstruir montos cuando solo tenemos factores guardados
    
    Obtiene una calificación de la base de datos.
    """
    # Verificar autenticación del usuario
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        # Importar Decimal para cálculos financieros precisos
        from decimal import Decimal
        
        # Obtener la calificación de MongoDB
        calificacion = Calificacion.objects.get(id=calificacion_id)
        
        # PREPARAR DATOS BÁSICOS DE LA CALIFICACIÓN
        # Convertir todos los campos a formato JSON-friendly
        calificacion_data = {
            'id': str(calificacion.id),  # ID como string
            'mercado': calificacion.Mercado or '',
            'origen': calificacion.Origen or '',
            'ejercicio': calificacion.Ejercicio or '',
            'instrumento': calificacion.Instrumento or '',
            'descripcion': calificacion.Descripcion or '',
            'fecha_pago': calificacion.FechaPago.isoformat() if calificacion.FechaPago else '',  # ISO format: "2024-01-15"
            'secuencia_evento': calificacion.SecuenciaEvento or '',
            'dividendo': str(calificacion.Dividendo or 0.0),
            'isfut': calificacion.ISFUT or False,
            'anho': calificacion.Anho or calificacion.Ejercicio or '',
            'valor_historico': str(calificacion.ValorHistorico or 0.0),
            'factor_actualizacion': str(calificacion.FactorActualizacion or 0.0),
            'montos': {},  # Diccionario para montos calculados
            'factores': {}  # Diccionario para factores guardados
        }
        
        # Obtener la SumaBase guardada
        # POR QUÉ: Necesitamos SumaBase para calcular montos desde factores
        suma_base = calificacion.SumaBase or Decimal(0)
        
        # CALCULAR MONTOS DESDE FACTORES (CÁLCULO INVERSO)
        # Si tenemos factores guardados y SumaBase, podemos reconstruir los montos
        # Fórmula: Monto = Factor * SumaBase
        for i in range(8, 38):
            # Obtener factor guardado
            factor_field = f'Factor{i:02d}'
            factor_value = getattr(calificacion, factor_field, Decimal(0))
            
            # Calcular monto desde el factor
            if suma_base > 0:
                # Monto = Factor * SumaBase
                # .quantize(Decimal('0.01')) redondea a 2 decimales (centavos)
                monto_calculado = (factor_value * suma_base).quantize(Decimal('0.01'))
            else:
                # Si SumaBase es 0, el monto también es 0
                monto_calculado = Decimal(0)
            
            # Guardar monto calculado
            monto_field = f'Monto{i:02d}'
            calificacion_data['montos'][monto_field] = str(monto_calculado) if monto_calculado else '0.0'
            
            # También incluir el factor guardado para referencia
            calificacion_data['factores'][factor_field] = str(factor_value) if factor_value else '0.0'
        
        # Retornar JSON con todos los datos
        return JsonResponse({
            'success': True,
            'calificacion': calificacion_data
        })
    except Calificacion.DoesNotExist:
        # Si la calificación no existe, retornar error
        return JsonResponse({'success': False, 'error': 'Calificación no encontrada'}, status=404)
    except Exception as e:
        # Si ocurre cualquier otro error, capturarlo
        return JsonResponse({'success': False, 'error': f'Error al obtener calificación: {str(e)}'}, status=500)


# =====================================================================
# VISTAS DE ELIMINAR CALIFICACIÓN
# =====================================================================
@require_POST
def eliminar_calificacion_view(request, calificacion_id):
    """
    Vista para eliminar una calificación.
    
    POR QUÉ ESTA FUNCIÓN ES IMPORTANTE:
    - Permite eliminar calificaciones del sistema
    - Maneja limpieza de registros de CSV cuando se eliminan todas las calificaciones
    - Registra la eliminación en logs de auditoría
    - Permite re-subir archivos CSV si se eliminan todas sus calificaciones
    
    CÓMO FUNCIONA:
    1. Verifica autenticación del usuario
    2. Obtiene la calificación a eliminar
    3. Si viene de CSV, guarda el hash del archivo
    4. Elimina la calificación
    5. Si era la última calificación del CSV, elimina el registro de ArchivoCSV
    6. Crea log de auditoría
    
    MANEJO DE CSV:
    - Si se eliminan todas las calificaciones de un CSV, se elimina el registro de ArchivoCSV
    - Esto permite volver a subir el mismo archivo CSV sin problemas de duplicados
    
    Elimina una calificación de la base de datos.
    """
    # Verificar autenticación del usuario
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    # Obtener usuario actual
    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401)

    try:
        # Obtener la calificación a eliminar
        calificacion = Calificacion.objects.get(id=calificacion_id)
        
        # Si la calificación proviene de un CSV, guardar el hash antes de eliminar
        # POR QUÉ: Necesitamos el hash para verificar si quedan más calificaciones del mismo archivo
        hash_archivo_csv = None
        if calificacion.Origen == 'csv' and hasattr(calificacion, 'hash_archivo_csv') and calificacion.hash_archivo_csv:
            hash_archivo_csv = calificacion.hash_archivo_csv
        
        # Eliminar la calificación de MongoDB
        calificacion.delete()
        
        # MANEJO DE ARCHIVOS CSV
        # Si la calificación venía de un CSV, verificar si quedan más calificaciones
        if hash_archivo_csv:
            from .models import ArchivoCSV
            
            # Contar cuántas calificaciones quedan con ese hash
            calificaciones_restantes = Calificacion.objects(
                Origen='csv',
                hash_archivo_csv=hash_archivo_csv
            ).count()
            
            # Si no quedan calificaciones de ese archivo, eliminar el registro de ArchivoCSV
            # POR QUÉ: Esto permite volver a subir el mismo archivo CSV sin problemas
            if calificaciones_restantes == 0:
                archivo_csv = ArchivoCSV.objects(hash_archivo=hash_archivo_csv).first()
                if archivo_csv:
                    archivo_csv.delete()
                    print(f"[ELIMINAR] Se eliminó el registro de ArchivoCSV (hash: {hash_archivo_csv}) porque no quedan calificaciones")
        
        # Crear log de auditoría
        # NOTA: calificacion ya fue eliminado, pero _crear_log puede manejar esto
        _crear_log(current_user, 'Eliminar Calificacion', documento_afectado=calificacion)
        
        return JsonResponse({'success': True, 'message': 'Calificación eliminada exitosamente'})
    except Calificacion.DoesNotExist:
        # Si la calificación no existe, retornar error
        return JsonResponse({'success': False, 'error': 'Calificación no encontrada'}, status=404)
    except Exception as e:
        # Si ocurre cualquier otro error, capturarlo
        return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'}, status=500)

# =====================================================================
# VISTAS DE COPIAR CALIFICACIÓN
# =====================================================================

@require_POST
def copiar_calificacion_view(request, calificacion_id):
    """
    Vista para copiar una calificación completa con un nuevo ID.
    
    POR QUÉ ESTA FUNCIÓN ES ÚTIL:
    - Permite duplicar calificaciones existentes
    - Útil para crear variaciones de una calificación base
    - Copia todos los campos: datos básicos, factores, montos, SumaBase
    - La nueva calificación tiene un ID único (nuevo documento en MongoDB)
    
    CÓMO FUNCIONA:
    1. Obtiene la calificación original
    2. Crea un nuevo objeto Calificacion vacío
    3. Copia todos los campos básicos uno por uno
    4. Copia todos los factores (Factor08 a Factor37)
    5. Copia todos los montos (Monto08 a Monto37)
    6. Copia SumaBase
    7. Establece nueva FechaAct
    8. Guarda la nueva calificación
    9. Crea log de auditoría
    
    Copia una calificación de la base de datos.
    """
    print(f"[COPiar] Iniciando copia de calificación ID: {calificacion_id}")
    
    # Verificar autenticación del usuario
    if 'user_id' not in request.session:
        print("[COPiar] Error: No autenticado")
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    # Obtener usuario actual
    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
        print(f"[COPiar] Usuario autenticado: {current_user.correo}")
    except usuarios.DoesNotExist:
        print("[COPiar] Error: Usuario no válido")
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401)

    try:
        # Importar Decimal para manejar valores numéricos
        from decimal import Decimal
        
        # Obtener la calificación original de MongoDB
        print(f"[COPiar] Obteniendo calificación original: {calificacion_id}")
        calificacion_original = Calificacion.objects.get(id=calificacion_id)
        print(f"[COPiar] Calificación encontrada: {calificacion_original.Instrumento}")
        
        # Crear un nuevo objeto Calificacion vacío
        # Este tendrá un nuevo ObjectId automáticamente al guardar
        nueva_calificacion = Calificacion()
        
        # COPIAR CAMPOS BÁSICOS
        # Copiar todos los campos de datos básicos uno por uno
        nueva_calificacion.Mercado = calificacion_original.Mercado
        nueva_calificacion.Origen = calificacion_original.Origen
        nueva_calificacion.Ejercicio = calificacion_original.Ejercicio
        nueva_calificacion.Instrumento = calificacion_original.Instrumento
        nueva_calificacion.EventoCapital = calificacion_original.EventoCapital
        nueva_calificacion.FechaPago = calificacion_original.FechaPago
        nueva_calificacion.SecuenciaEvento = calificacion_original.SecuenciaEvento
        nueva_calificacion.Descripcion = calificacion_original.Descripcion
        nueva_calificacion.Dividendo = calificacion_original.Dividendo
        nueva_calificacion.ISFUT = calificacion_original.ISFUT
        nueva_calificacion.ValorHistorico = calificacion_original.ValorHistorico
        nueva_calificacion.FactorActualizacion = calificacion_original.FactorActualizacion
        nueva_calificacion.Anho = calificacion_original.Anho
        nueva_calificacion.RentasExentas = calificacion_original.RentasExentas
        nueva_calificacion.Factor19A = calificacion_original.Factor19A
        
        # COPIAR TODOS LOS FACTORES (Factor08 a Factor37)
        # Iterar sobre todos los factores y copiarlos
        print("[COPiar] Copiando factores...")
        for i in range(8, 38):
            factor_field = f'Factor{i:02d}'
            # Obtener valor del factor original
            valor_factor = getattr(calificacion_original, factor_field, Decimal(0))
            # Asignar valor a la nueva calificación
            setattr(nueva_calificacion, factor_field, valor_factor)
        
        # COPIAR TODOS LOS MONTOS (Monto08 a Monto37)
        # Iterar sobre todos los montos y copiarlos
        print("[COPiar] Copiando montos...")
        for i in range(8, 38):
            monto_field = f'Monto{i:02d}'
            # Obtener valor del monto original
            valor_monto = getattr(calificacion_original, monto_field, Decimal(0))
            # Asignar valor a la nueva calificación
            setattr(nueva_calificacion, monto_field, valor_monto)
        
        # Copiar SumaBase
        nueva_calificacion.SumaBase = calificacion_original.SumaBase
        
        # Establecer nueva fecha de actualización
        # POR QUÉ: La nueva calificación debe tener su propia fecha de creación
        nueva_calificacion.FechaAct = datetime.datetime.now()
        
        # Guardar la nueva calificación en MongoDB
        # Esto generará un nuevo ObjectId automáticamente
        print("[COPiar] Guardando nueva calificación...")
        nueva_calificacion.save()
        print(f"[COPiar] Nueva calificación guardada con ID: {nueva_calificacion.id}")
        
        # Crear log de auditoría
        # Registra que se creó una nueva calificación (copiada de otra)
        try:
            _crear_log(current_user, 'Crear Calificacion', documento_afectado=nueva_calificacion)
            print("[COPiar] Log creado exitosamente")
        except Exception as log_error:
            # Si falla el log, no detener la operación
            print(f"[COPiar] Advertencia: Error al crear log: {log_error}")
        
        # Retornar éxito con el ID de la nueva calificación
        return JsonResponse({
            'success': True,
            'message': 'Calificación copiada exitosamente',
            'nueva_calificacion_id': str(nueva_calificacion.id)  # ID para que JavaScript pueda usarlo
        })
        
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
    
    POR QUÉ ESTA FUNCIÓN ES IMPORTANTE:
    - Permite previsualizar CSV antes de cargarlo
    - Valida formato y estructura del CSV
    - Detecta archivos duplicados usando hash SHA-256
    - Muestra datos en tabla para que el usuario los revise
    
    CÓMO FUNCIONA:
    1. Recibe archivo CSV con factores ya calculados
    2. Calcula hash SHA-256 del contenido
    3. Verifica si el archivo ya fue subido (duplicado)
    4. Lee y valida el CSV con pandas
    5. Retorna datos para mostrar en tabla de previsualización
    
    DETECCIÓN DE DUPLICADOS:
    - Usa hash SHA-256 del contenido del archivo
    - Compara con registros en ArchivoCSV
    - Evita cargar el mismo archivo múltiples veces
    
    Lee un archivo CSV que contiene factores ya calculados.
    Valida el formato y retorna los datos para mostrarlos en una tabla de previsualización.
    Calcula un hash único del contenido para evitar duplicados.
    
    Argumentos:
        request: Objeto HttpRequest de Django (solo POST permitido)
        
    Returns (lo que devuelve la funcion):
        JsonResponse: JSON con datos del CSV para previsualizar, incluyendo hash del archivo
    """
    # Verificar autenticación del usuario
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    # Obtener usuario actual
    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401)

    try:
        # Importar librerías necesarias
        import pandas as pd  # Para leer y procesar CSV
        from decimal import Decimal  # Para precisión financiera
        import hashlib  # Para calcular hash del archivo
        
        # Verificar que se recibió un archivo
        if 'archivo' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No se recibió ningún archivo'}, status=400)
        
        archivo = request.FILES['archivo']
        
        # CALCULAR HASH DEL ARCHIVO
        # POR QUÉ: Identificar archivos duplicados incluso si tienen nombres diferentes
        archivo.seek(0)  # Asegurar que estamos al inicio del archivo
        contenido = archivo.read()
        # SHA-256 genera un hash único de 64 caracteres hexadecimales
        hash_archivo = hashlib.sha256(contenido).hexdigest()
        archivo.seek(0)  # Volver al inicio para leer el CSV con pandas
        
        # VERIFICAR SI EL ARCHIVO YA FUE SUBIDO
        from .models import ArchivoCSV
        archivo_existente = ArchivoCSV.objects(hash_archivo=hash_archivo).first()
        if archivo_existente:
            # Verificar si todavía existen calificaciones con este hash
            # POR QUÉ: Si se eliminaron todas las calificaciones, se puede volver a subir
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
    """
    Vista AJAX para previsualizar archivo CSV con montos.
    
    POR QUÉ ESTA FUNCIÓN ES IMPORTANTE:
    - Permite previsualizar CSV con montos antes de cargarlo
    - Similar a preview_factor_view pero para montos
    - Valida formato y estructura del CSV
    - Detecta archivos duplicados usando hash SHA-256
    - Muestra datos en tabla para que el usuario los revise
    
    CÓMO FUNCIONA:
    1. Recibe archivo CSV con montos (dinero)
    2. Calcula hash SHA-256 del contenido
    3. Verifica si el archivo ya fue subido (duplicado)
    4. Lee y valida el CSV con pandas
    5. Retorna datos para mostrar en tabla de previsualización
    
    DIFERENCIA CON preview_factor_view:
    - preview_factor_view: CSV con factores ya calculados
    - preview_monto_view: CSV con montos (se calcularán factores después)
    
    Previsualiza un archivo CSV que contiene montos ya calculados.
    """
    # Verificar autenticación del usuario
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    # Obtener usuario actual
    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401)

    try:
        # Importar librerías necesarias
        import pandas as pd  # Para leer y procesar CSV
        from decimal import Decimal  # Para precisión financiera
        import hashlib  # Para calcular hash del archivo
        
        # Verificar que se recibió un archivo
        if 'archivo' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No se recibió ningún archivo'}, status=400)
        
        archivo = request.FILES['archivo']
        
        # CALCULAR HASH DEL ARCHIVO
        # POR QUÉ: Identificar archivos duplicados incluso si tienen nombres diferentes
        archivo.seek(0)  # Asegurar que estamos al inicio del archivo
        contenido = archivo.read()
        # SHA-256 genera un hash único de 64 caracteres hexadecimales
        hash_archivo = hashlib.sha256(contenido).hexdigest()
        archivo.seek(0)  # Volver al inicio para leer el CSV con pandas
        
        # VERIFICAR SI EL ARCHIVO YA FUE SUBIDO
        from .models import ArchivoCSV
        archivo_existente = ArchivoCSV.objects(hash_archivo=hash_archivo).first()
        if archivo_existente:
            # Verificar si todavía existen calificaciones con este hash
            # POR QUÉ: Si se eliminaron todas las calificaciones, se puede volver a subir
            calificaciones_existentes = Calificacion.objects(
                Origen='csv',
                hash_archivo_csv=hash_archivo
            ).count()
            
            print(f"[PREVIEW_MONTO] Archivo duplicado encontrado. Calificaciones existentes con hash {hash_archivo}: {calificaciones_existentes}")
            
            # Si no hay calificaciones con ese hash, eliminar el registro de ArchivoCSV
            # POR QUÉ: Permitir volver a subir el archivo si se eliminaron todas las calificaciones
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
        
        # LEER CSV CON PANDAS
        # Intentar diferentes encodings para manejar caracteres especiales
        try:
            # Primero intentar UTF-8 (estándar moderno)
            df = pd.read_csv(archivo, encoding='utf-8')
        except UnicodeDecodeError:
            # Si falla, intentar Latin-1 (común en archivos antiguos)
            archivo.seek(0)
            df = pd.read_csv(archivo, encoding='latin-1')
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al leer el archivo CSV: {str(e)}'}, status=400)
        
        # Limpiar nombres de columnas (eliminar espacios al inicio y final)
        df.columns = df.columns.str.strip()
        
        # Eliminar filas completamente vacías
        df = df.dropna(how='all')
        
        # Convertir a lista de diccionarios para procesar
        datos = []  # Lista para datos válidos
        errores = []  # Lista para errores encontrados
        
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
    """
    Vista AJAX para calcular factores desde montos en carga masiva.
    
    POR QUÉ ESTA FUNCIÓN ES CRÍTICA:
    - Calcula factores para múltiples filas de CSV a la vez
    - Optimiza el proceso de carga masiva
    - Aplica la misma fórmula que calcular_factores_view pero en lote
    - Valida que factores no excedan 1.0 (100%)
    
    CÓMO FUNCIONA:
    1. Recibe lista de filas CSV con montos (JSON)
    2. Para cada fila:
       a. Extrae montos (F8 MONT a F37 MONT)
       b. Calcula SumaBase (suma de montos 8-19)
       c. Calcula factores: Factor = Monto / SumaBase
       d. Valida que factores no excedan 1.0
    3. Retorna todas las filas con factores calculados
    
    FÓRMULA:
    - SumaBase = suma de montos del 8 al 19
    - Factor = Monto / SumaBase (para cada monto del 8 al 37)
    - Factor máximo = 1.0 (si excede, se ajusta a 1.0)
    
    Vista para calcular factores desde montos en carga masiva
    """
    # Verificar autenticación del usuario
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        import json
        from decimal import Decimal
        
        # Parsear JSON del body
        data = json.loads(request.body)
        datos_csv = data.get('datos', [])
        
        # Validar que se recibieron datos
        if not datos_csv:
            return JsonResponse({'success': False, 'error': 'No se recibieron datos'}, status=400)
        
        # Lista para almacenar filas con factores calculados
        datos_calculados = []
        
        # PROCESAR CADA FILA DEL CSV
        for fila in datos_csv:
            # Copiar la fila original para no modificar el original
            fila_calculada = fila.copy()
            
            # OBTENER MONTOS Y CALCULAR SUMA BASE
            montos = []
            suma_base = Decimal(0)
            
            # Iterar sobre todos los montos del 8 al 37
            for i in range(8, 38):
                # Intentar diferentes nombres de columnas (variaciones en el CSV)
                monto_key = f'F{i} MONT' if f'F{i} MONT' in fila else f'F{i} M'
                monto_value = fila.get(monto_key, '0.0')
                
                try:
                    # Convertir a Decimal
                    monto_decimal = Decimal(str(monto_value))
                    montos.append(monto_decimal)
                    
                    # Solo sumar montos del 8 al 19 para SumaBase
                    if i <= 19:
                        suma_base += monto_decimal
                except:
                    # Si hay error, usar 0
                    montos.append(Decimal(0))
            
            # CALCULAR FACTORES
            if suma_base > 0:
                # Precisión de 8 decimales
                EIGHT_PLACES = Decimal('0.00000001')
                
                # Calcular cada factor
                for i in range(8, 38):
                    # Factor = Monto / SumaBase
                    factor = (montos[i - 8] / suma_base).quantize(EIGHT_PLACES)
                    
                    # Validar que el factor no exceda 1.0 (100%)
                    # POR QUÉ: Un factor > 1.0 no tiene sentido financiero
                    if factor > 1:
                        factor = Decimal(1)
                    
                    # Guardar factor en la fila calculada
                    fila_calculada[f'F{i}'] = str(factor)
            else:
                # Si SumaBase es 0, todos los factores son 0
                for i in range(8, 38):
                    fila_calculada[f'F{i}'] = '0.0'
            
            # Agregar fila calculada a la lista
            datos_calculados.append(fila_calculada)
        
        # Retornar todas las filas con factores calculados
        return JsonResponse({
            'success': True,
            'datos_calculados': datos_calculados
        })
        
    except Exception as e:
        # Si ocurre cualquier error, capturarlo y retornar error
        print(f"Error al calcular factores masivo: {e}")
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': f'Error al calcular: {str(e)}'}, status=500)


@require_GET
def obtener_logs_calificacion_view(request, calificacion_id):
    """
    Vista AJAX para obtener los logs de una calificación específica.
    
    POR QUÉ ESTA FUNCIÓN ES ÚTIL:
    - Permite ver el historial completo de cambios de una calificación
    - Muestra quién hizo qué cambios y cuándo
    - Útil para auditoría y debugging
    - Muestra cambios detallados en formato legible
    
    CÓMO FUNCIONA:
    1. Obtiene la calificación por ID
    2. Busca todos los logs relacionados con esa calificación
    3. Procesa cada log para extraer información del actor y cambios
    4. Retorna logs en formato JSON para mostrar en la interfaz
    
    Vista para obtener los logs de una calificación específica
    """
    # Verificar autenticación del usuario
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    # Obtener usuario actual
    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401)

    try:
        # Obtener la calificación de MongoDB
        calificacion = Calificacion.objects.get(id=calificacion_id)
        
        # Obtener información básica de la calificación
        # Para mostrar contexto en la interfaz
        calificacion_info = {
            'ejercicio': calificacion.Ejercicio or '',
            'instrumento': calificacion.Instrumento or '',
            'mercado': calificacion.Mercado or ''
        }
        
        # Obtener todos los logs relacionados con esta calificación
        # iddocumento es una ReferenceField que apunta a la calificación
        # .order_by('-fecharegistrada') ordena por fecha descendente (más recientes primero)
        logs_raw = Log.objects(iddocumento=calificacion).order_by('-fecharegistrada')
        logs_procesados = []
        
        # PROCESAR CADA LOG
        for l in logs_raw:
            # ACTOR (usuario que ejecutó la acción)
            # Obtener correo del actor (siempre está guardado)
            actor_correo = getattr(l, "correoElectronico", "N/A")
            actor_id = "N/A"
            actor_nombre = "N/A"
            
            # Intentar obtener ID y nombre del actor
            if hasattr(l, "Usuarioid") and l.Usuarioid:
                actor_id_obj = _extraer_object_id(l.Usuarioid)
                if actor_id_obj:
                    actor_id = str(actor_id_obj)
                    try:
                        # Intentar obtener nombre del actor si aún existe
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