import json  # Para manejar datos JSON en las respuestas de API (crear_usuario_view, eliminar_usuarios_view, etc.)
import bcrypt  # Para hashear contraseñas de forma segura
import re  # Para expresiones regulares - usado en _extraer_object_id() para parsear DBRef y extraer ObjectIds
import os  # Para operaciones del sistema de archivos usado en _guardar_foto_perfil() para manejar rutas y extensiones
import datetime  # Para manejar fechas y horas
from django.shortcuts import render, redirect  # render: renderizar templates HTML | redirect: redirigir a otras URLs
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseServerError  # Respuestas HTTP: Forbidden(403), JSON, ServerError(500)
from django.views.decorators.http import require_POST, require_GET  # Decoradores para restringir métodos HTTP (POST/GET)
from django.contrib import messages  # Para mensajes flash al usuario
from django.conf import settings  # Acceso a configuración de Django usado en _guardar_foto_perfil() para MEDIA_ROOT
from mongoengine.errors import DoesNotExist  # Excepción cuando un documento no existe en MongoDB
from bson import ObjectId  # Tipo ObjectId de MongoDB - usado en _extraer_object_id() y operaciones con IDs
try:
    from PIL import Image  # librería para procesamiento de imágenes - usado en _guardar_foto_perfil() para redimensionar fotos
    HAS_PIL = True
except ImportError:
    HAS_PIL = False  # Si no está instalado Pillow, las imágenes no se redimensionarán pero la app funcionará
from .formulario import LoginForm, CalificacionModalForm, UsuarioForm, UsuarioUpdateForm, FactoresForm, MontosForm  # Formularios Django para validación de datos
from .models import usuarios, Calificacion, Log  # Modelos de MongoDB (Documentos) para interactuar con la base de datos


# --- Función Auxiliar para extraer ObjectId de DBRef o ObjectId ---
def _extraer_object_id(valor):
    """
    Extrae el ObjectId desde un DBRef, ObjectId o cualquier otro tipo.
    Retorna el string del ObjectId o None si no puede extraerlo.
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
# --- Fin Función Auxiliar ---


#Función Auxiliar para manejar fotos de perfil
def _guardar_foto_perfil(archivo, usuario_id):#Guarda la foto de perfil del usuario y retorna la ruta. Redimensiona la imagen si es muy grande.
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
# --- Fin Función Auxiliar ---


# --- Funciones auxiliares para hashear contraseñas ---
def _hash_password(password):
    """Hashea una contraseña usando bcrypt"""
    if not password:
        return None
    # Generar salt y hashear la contraseña
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def _check_password(password, hashed_password):
    """Verifica si una contraseña coincide con su hash"""
    if not password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

#Función para crear logs
def _crear_log(usuario_obj, accion_str, documento_afectado=None, usuario_afectado=None, cambios_detallados=None):#Guarda un registro de log con información sobre la acción realizada.
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
            cambios_detallados=cambios_json
        )
        nuevo_log.save()
        print(f"Log guardado correctamente: {accion_str} por {usuario_obj.correo}")
    except Exception as e:
        print(f"¡¡ADVERTENCIA!! Falló al guardar el log: {e}")
# --- Fin Función Auxiliar ---


def listar_usuarios(request):
    todos_los_usuarios = usuarios.objects.all()
    return render(request, 'prueba/listar.html', {'usuarios': todos_los_usuarios})


def login_view(request):
    if 'user_id' in request.session:
        return redirect('home')

    form = LoginForm()
    error = None

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            correo_usuario = form.cleaned_data['correo']
            contrasena_usuario = form.cleaned_data['contrasena']

            try:
                user = usuarios.objects.get(correo=correo_usuario)
                # Verificar contraseña usando bcrypt
                if not _check_password(contrasena_usuario, user.contrasena):
                    user = None
            except usuarios.DoesNotExist:
                user = None

            if user:
                request.session['user_id'] = str(user.id)
                request.session['user_nombre'] = user.nombre
                return redirect('home')
            else:
                error = "Correo o contraseña incorrectos."

    return render(request, 'prueba/login.html', {'form': form, 'error': error})


def home_view(request):
    if 'user_id' not in request.session:
        return redirect('login')

    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
        is_admin = current_user.rol
    except usuarios.DoesNotExist:
        request.session.flush()
        return redirect('login')

    # Obtener calificaciones
    calificaciones = []
    if request.method == 'GET':
        mercado_raw = request.GET.get('mercado', '')
        origen = request.GET.get('origen', '')
        periodo = request.GET.get('periodo', '')
        
        # Normalizar mercado a los valores válidos (acciones, CFI, Fondos mutuos)
        mercado_normalizado = mercado_raw
        if mercado_raw and mercado_raw != 'Todos':
            mercado_lower = mercado_raw.lower().strip()
            if mercado_lower == 'acciones' or mercado_lower == 'accion':
                mercado_normalizado = 'acciones'
            elif mercado_lower == 'cfi':
                mercado_normalizado = 'CFI'
            elif mercado_lower == 'fondos mutuos' or mercado_lower == 'fondosmutuos' or mercado_lower == 'fondo mutuo':
                mercado_normalizado = 'Fondos mutuos'
            else:
                mercado_normalizado = mercado_raw  # Mantener el valor original si no coincide
        
        # Normalizar origen a los valores válidos (csv, corredor)
        origen_normalizado = origen
        if origen:
            origen_lower = origen.lower().strip()
            if origen_lower == 'csv':
                origen_normalizado = 'csv'
            elif origen_lower == 'corredor':
                origen_normalizado = 'corredor'
        
        query = {}
        if mercado_normalizado and mercado_normalizado != 'Todos':
            query['Mercado'] = mercado_normalizado
        if origen_normalizado:
            query['Origen'] = origen_normalizado
        if periodo:
            try:
                periodo_int = int(periodo)
                query['Ejercicio'] = periodo_int
            except ValueError:
                pass
        
        # Solo cargar calificaciones si hay filtros aplicados
        # Si no hay filtros, no cargar ninguna calificación
        if query:
            calificaciones = Calificacion.objects(**query).order_by('-FechaAct')
        else:
            calificaciones = []

    # Serializar calificaciones a formato JSON para el JavaScript (mismo formato que buscar_calificaciones_view)
    import json
    calificaciones_data = []
    for cal in calificaciones:
        # Asegurar que el ID esté disponible
        cal_id = str(cal.id) if cal.id else ''
        if not cal_id:
            continue  # Saltar calificaciones sin ID
        
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
        for i in range(8, 38):
            field_name = f'Factor{i:02d}'
            valor = getattr(cal, field_name, 0.0)
            cal_data['factores'][field_name] = str(valor) if valor else '0.0'
        
        calificaciones_data.append(cal_data)
    
    calificaciones_json = json.dumps(calificaciones_data)
    
    return render(request, 'prueba/home.html', {
        'user_nombre': current_user.nombre,
        'is_admin': is_admin,
        'current_user': current_user,
        'calificaciones': calificaciones,
        'calificaciones_json': calificaciones_json
    })


@require_GET
def buscar_calificaciones_view(request):
    """Vista para buscar calificaciones según filtros de mercado, origen y periodo"""
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        mercado_raw = request.GET.get('mercado', '').strip()
        origen = request.GET.get('origen', '').strip()
        periodo = request.GET.get('periodo', '').strip()

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

        # Normalizar origen a los valores válidos (csv, corredor)
        origen_normalizado = origen
        if origen:
            origen_lower = origen.lower().strip()
            if origen_lower == 'csv':
                origen_normalizado = 'csv'
            elif origen_lower == 'corredor':
                origen_normalizado = 'corredor'
        
        # Construir query de filtrado
        query = {}
        if mercado_normalizado and mercado_normalizado != 'Todos':
            query['Mercado'] = mercado_normalizado
        if origen_normalizado:
            query['Origen'] = origen_normalizado
        if periodo:
            try:
                periodo_int = int(periodo)
                query['Ejercicio'] = periodo_int
            except ValueError:
                pass

        # Buscar calificaciones (si no hay filtros, devolver todas)
        if query:
            calificaciones = Calificacion.objects(**query).order_by('-FechaAct')
        else:
            # Si no hay filtros, devolver todas las calificaciones
            calificaciones = Calificacion.objects().order_by('-FechaAct')

        # Convertir a formato JSON
        calificaciones_data = []
        for cal in calificaciones:
            # Asegurar que el ID esté disponible
            cal_id = str(cal.id) if cal.id else ''
            if not cal_id:
                print(f"ADVERTENCIA: Calificación sin ID: {cal}")
                continue  # Saltar calificaciones sin ID
            
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
            for i in range(8, 38):
                field_name = f'Factor{i:02d}'
                valor = getattr(cal, field_name, 0.0)
                cal_data['factores'][field_name] = str(valor) if valor else '0.0'
            
            calificaciones_data.append(cal_data)

        return JsonResponse({
            'success': True,
            'calificaciones': calificaciones_data,
            'total': len(calificaciones_data)
        })

    except Exception as e:
        print(f"Error al buscar calificaciones: {e}")
        return JsonResponse({'success': False, 'error': f'Error al buscar: {str(e)}'}, status=500)


def logout_view(request):
    request.session.flush()
    return redirect('login')


def ingresar_view(request):
    if 'user_id' not in request.session:
        return redirect('login')

    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
    except usuarios.DoesNotExist:
        request.session.flush()
        return redirect('login')

    if request.method == 'POST':
        form = CalificacionModalForm(request.POST)
        if form.is_valid():
            # Convertir FechaPago de string a DateTime si viene como string
            cleaned_data = form.cleaned_data.copy()
            if 'FechaPago' in cleaned_data and cleaned_data['FechaPago']:
                if isinstance(cleaned_data['FechaPago'], str):
                    from datetime import datetime
                    try:
                        cleaned_data['FechaPago'] = datetime.strptime(cleaned_data['FechaPago'], '%Y-%m-%d')
                    except:
                        pass
            
            # Validar que SecuenciaEvento sea mayor a 10000
            if 'SecuenciaEvento' in cleaned_data and cleaned_data['SecuenciaEvento']:
                if cleaned_data['SecuenciaEvento'] <= 10000:
                    return JsonResponse({'success': False, 'error': 'La secuencia de evento debe ser mayor a 10,000.'}, status=400)
            
            # Normalizar mercado antes de guardar
            mercado_raw = cleaned_data.get('Mercado', '')
            if mercado_raw:
                mercado_lower = mercado_raw.lower().strip()
                if mercado_lower == 'acciones' or mercado_lower == 'accion':
                    cleaned_data['Mercado'] = 'acciones'
                elif mercado_lower == 'cfi':
                    cleaned_data['Mercado'] = 'CFI'
                elif mercado_lower == 'fondos mutuos' or mercado_lower == 'fondosmutuos' or mercado_lower == 'fondo mutuo':
                    cleaned_data['Mercado'] = 'Fondos mutuos'
            
            # Normalizar origen antes de guardar
            origen_raw = cleaned_data.get('Origen', 'corredor')
            if origen_raw:
                origen_lower = origen_raw.lower().strip()
                if origen_lower == 'csv':
                    cleaned_data['Origen'] = 'csv'
                elif origen_lower == 'corredor' or origen_lower == 'manual':
                    cleaned_data['Origen'] = 'corredor'
            else:
                cleaned_data['Origen'] = 'corredor'  # Valor por defecto
            
            # Verificar si es una actualización o creación
            calificacion_id = request.POST.get('calificacion_id')
            if calificacion_id:
                # Actualizar calificación existente
                try:
                    calificacion = Calificacion.objects.get(id=calificacion_id)
                    # Capturar cambios antes de actualizar
                    cambios_detallados = []
                    campos_actualizados = False
                    
                    for key, value in cleaned_data.items():
                        # Verificar si el campo fue enviado en el POST original
                        if key in request.POST:
                            # Obtener valor actual antes de modificar
                            valor_actual = getattr(calificacion, key, None)
                            
                            # Formatear valores para comparación y visualización
                            def formatear_valor(val):
                                if val is None:
                                    return None
                                if isinstance(val, datetime.datetime):
                                    return val.strftime('%Y-%m-%d %H:%M:%S')
                                if isinstance(val, bool):
                                    return 'Sí' if val else 'No'
                                return str(val)
                            
                            valor_anterior_str = formatear_valor(valor_actual)
                            valor_nuevo_str = formatear_valor(value)
                            
                            # Solo actualizar si el valor es diferente del actual
                            cambio_realizado = False
                            
                            # Para campos booleanos, comparar directamente
                            if isinstance(value, bool):
                                if valor_actual != value:
                                    setattr(calificacion, key, value)
                                    campos_actualizados = True
                                    cambio_realizado = True
                            # Para campos numéricos, comparar valores
                            elif isinstance(value, (int, float)):
                                if valor_actual != value:
                                    setattr(calificacion, key, value)
                                    campos_actualizados = True
                                    cambio_realizado = True
                            # Para strings, actualizar si no está vacío y es diferente
                            elif isinstance(value, str):
                                if value.strip() != '' and valor_actual != value:
                                    setattr(calificacion, key, value)
                                    campos_actualizados = True
                                    cambio_realizado = True
                            # Para fechas y otros tipos, comparar si no es None
                            elif value is not None:
                                if valor_actual != value:
                                    setattr(calificacion, key, value)
                                    campos_actualizados = True
                                    cambio_realizado = True
                            
                            # Si hubo cambio, agregar a la lista de cambios
                            if cambio_realizado:
                                cambios_detallados.append({
                                    'campo': key,
                                    'valor_anterior': valor_anterior_str,
                                    'valor_nuevo': valor_nuevo_str
                                })
                    
                    # Actualizar fecha de modificación solo si realmente se modificó algo
                    if campos_actualizados:
                        calificacion.FechaAct = datetime.datetime.now()
                        calificacion.save()
                        _crear_log(current_user, 'Modificar Calificacion', documento_afectado=calificacion, cambios_detallados=cambios_detallados if cambios_detallados else None)
                    else:
                        _crear_log(current_user, 'Modificar Calificacion', documento_afectado=calificacion)
                    return JsonResponse({
                        'success': True,
                        'calificacion_id': str(calificacion.id),
                        'data': {
                            'mercado': calificacion.Mercado or '',
                            'origen': calificacion.Origen or '',
                            'instrumento': calificacion.Instrumento or '',
                            'evento_capital': calificacion.EventoCapital or '',
                            'fecha_pago': calificacion.FechaPago.strftime('%Y-%m-%d') if calificacion.FechaPago else '',
                            'secuencia': calificacion.SecuenciaEvento or '',
                            'anho': calificacion.Anho or calificacion.Ejercicio or '',
                            'valor_historico': str(calificacion.ValorHistorico or 0.0),
                            'descripcion': calificacion.Descripcion or ''
                        }
                    })
                except Calificacion.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Calificación no encontrada.'}, status=404)
            else:
                # Crear nueva calificación
                nueva_calificacion = Calificacion(**cleaned_data)
                nueva_calificacion.save()
                _crear_log(current_user, 'Crear Calificacion', documento_afectado=nueva_calificacion)
                # Retornar JSON con el ID de la calificación para abrir el segundo modal
                return JsonResponse({
                    'success': True,
                    'calificacion_id': str(nueva_calificacion.id),
                    'data': {
                        'mercado': nueva_calificacion.Mercado or '',
                        'origen': nueva_calificacion.Origen or '',
                        'instrumento': nueva_calificacion.Instrumento or '',
                        'evento_capital': nueva_calificacion.EventoCapital or '',
                        'fecha_pago': nueva_calificacion.FechaPago.strftime('%Y-%m-%d') if nueva_calificacion.FechaPago else '',
                        'secuencia': nueva_calificacion.SecuenciaEvento or '',
                        'anho': nueva_calificacion.Anho or nueva_calificacion.Ejercicio or '',
                        'valor_historico': str(nueva_calificacion.ValorHistorico or 0.0),
                        'descripcion': nueva_calificacion.Descripcion or ''
                    }
                })
        else:
            return JsonResponse({'success': False, 'error': form.errors.as_json()}, status=400)
    else:
        initial_data = {
            'Mercado': request.GET.get('mercado'),
            'Ejercicio': request.GET.get('ejercicio'),
            'Instrumento': request.GET.get('instrumento'),
            'FechaPago': request.GET.get('fecha_pago'),
            'SecuenciaEvento': request.GET.get('secuencia'),
        }
        form = CalificacionModalForm(initial=initial_data)

    return render(request, 'prueba/ingresar.html', {'form': form})


def ingresar_calificacion(request):
    """
    Vista para ingresar calificaciones con MONTOS.
    El usuario ingresa montos (dinero), y el sistema calcula los factores automáticamente.
    Según los requisitos: todos los factores (8-37) se calculan dividiendo cada monto por la Suma Base (suma de montos 8-19).
    """
    if 'user_id' not in request.session:
        return redirect('login')
    
    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
    except usuarios.DoesNotExist:
        request.session.flush()
        return redirect('login')
    
    if request.method == 'POST':
        form = MontosForm(request.POST)
        
        if form.is_valid():
            try:
                from decimal import Decimal
                
                # 1. Obtener todos los montos del formulario (como objetos Decimal)
                montos = {}
                for i in range(8, 38):
                    monto_key = f'monto_{i}'
                    monto_value = form.cleaned_data.get(monto_key, Decimal(0))
                    # Convertir a Decimal si no lo es
                    if not isinstance(monto_value, Decimal):
                        montos[i] = Decimal(str(monto_value)) if monto_value else Decimal(0)
                    else:
                        montos[i] = monto_value
                
                # 2. ¡LA LÓGICA CLAVE! Calcular la Suma Base (suma de montos del 8 al 19)
                suma_base = Decimal(0)
                for i in range(8, 20):  # Del 8 al 19 inclusive
                    suma_base += montos.get(i, Decimal(0))
                
                # 3. Crear el objeto Calificacion para GUARDAR
                nueva_calificacion = Calificacion()
                
                # 4. Asignar los datos generales (usando nombres correctos del modelo)
                nueva_calificacion.Ejercicio = form.cleaned_data.get('Ejercicio')
                
                # Normalizar mercado antes de guardar
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
                
                # Normalizar origen antes de guardar
                origen_raw = form.cleaned_data.get('Origen', 'corredor')
                origen_normalizado = origen_raw
                if origen_raw:
                    origen_lower = origen_raw.lower().strip()
                    if origen_lower == 'csv':
                        origen_normalizado = 'csv'
                    elif origen_lower == 'corredor' or origen_lower == 'manual':
                        origen_normalizado = 'corredor'
                
                nueva_calificacion.Origen = origen_normalizado
                
                # 5. ¡LA MAGIA! Calcular y asignar cada FACTOR
                # El requisito dice "Decimal redondeado al 8vo decimal"
                EIGHT_PLACES = Decimal('0.00000001')
                
                if suma_base > 0:
                    # Calcular TODOS los factores (del 8 al 37) dividiendo cada monto por la Suma Base
                    for i in range(8, 38):
                        factor_field = f'Factor{i:02d}'  # Factor08, Factor09, etc.
                        monto = montos.get(i, Decimal(0))
                        factor_calculado = (monto / suma_base).quantize(EIGHT_PLACES)
                        setattr(nueva_calificacion, factor_field, factor_calculado)
                else:
                    # Si la suma es 0, todos los factores son 0
                    for i in range(8, 38):
                        factor_field = f'Factor{i:02d}'
                        setattr(nueva_calificacion, factor_field, Decimal(0))
                
                # 6. Guardar el objeto con los factores CALCULADOS
                nueva_calificacion.save()
                
                # 7. Crear el Log
                _crear_log(
                    current_user,
                    'Crear Calificacion',
                    documento_afectado=nueva_calificacion
                )
                
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


@require_POST
def guardar_factores_view(request):
    """Vista para guardar los factores calculados en la calificación"""
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401)

    calificacion_id = request.POST.get('calificacion_id')
    if not calificacion_id:
        return JsonResponse({'success': False, 'error': 'Falta calificacion_id'}, status=400)

    try:
        calificacion = Calificacion.objects.get(id=calificacion_id)
    except Calificacion.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Calificación no encontrada'}, status=404)

    try:
        from decimal import Decimal
        
        # Los factores ya fueron calculados y están en el formulario
        # IMPORTANTE: Los montos ya fueron guardados cuando se calcularon los factores
        # No debemos sobrescribir los montos aquí, solo guardar los factores calculados
        # Actualizar solo los factores que fueron enviados en el POST
        cambios_detallados = []
        factores_actualizados = False
        for i in range(8, 38):
            factor_field = f'Factor{i:02d}'
            valor_post = request.POST.get(factor_field)
            # Solo actualizar si el valor fue enviado (no None)
            if valor_post is not None:
                try:
                    valor_decimal = Decimal(str(valor_post)) if valor_post else Decimal(0)
                    # Solo actualizar si el valor es diferente al actual
                    valor_actual = getattr(calificacion, factor_field, Decimal(0))
                    if valor_decimal != valor_actual:
                        cambios_detallados.append({
                            'campo': factor_field,
                            'valor_anterior': str(valor_actual),
                            'valor_nuevo': str(valor_decimal)
                        })
                        setattr(calificacion, factor_field, valor_decimal)
                        factores_actualizados = True
                except (ValueError, TypeError):
                    # Si hay error, mantener el valor actual
                    pass
        
        # NO guardar montos aquí - ya fueron guardados cuando se calcularon los factores
        # Solo guardar los factores calculados
        # Actualizar la fecha de modificación solo si se actualizaron factores
        if factores_actualizados:
            calificacion.FechaAct = datetime.datetime.now()
            calificacion.save()
            _crear_log(current_user, 'Modificar Calificacion', documento_afectado=calificacion, cambios_detallados=cambios_detallados if cambios_detallados else None)
        else:
            _crear_log(current_user, 'Modificar Calificacion', documento_afectado=calificacion)
        return JsonResponse({'success': True})
    except Exception as e:
        print(f"Error al guardar factores: {e}")
        return JsonResponse({'success': False, 'error': f'Error al guardar: {str(e)}'}, status=500)


@require_POST
def calcular_factores_view(request):
    """Vista para calcular factores desde MONTOS ingresados"""
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401)

    calificacion_id = request.POST.get('calificacion_id')
    if not calificacion_id:
        return JsonResponse({'success': False, 'error': 'Falta calificacion_id'}, status=400)

    try:
        calificacion = Calificacion.objects.get(id=calificacion_id)
    except Calificacion.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Calificación no encontrada'}, status=404)

    try:
        from decimal import Decimal
        
        # 1. Obtener todos los MONTOS del formulario (el usuario ingresa dinero)
        montos = {}
        for i in range(8, 38):
            monto_key = f'monto_{i}'
            valor_post = request.POST.get(monto_key, '0.00')
            try:
                montos[i] = Decimal(str(valor_post)) if valor_post else Decimal(0)
            except (ValueError, TypeError):
                montos[i] = Decimal(0)

        # 2. Calcular la Suma Base (suma de montos del 8 al 19)
        suma_base = Decimal(0)
        for i in range(8, 20):  # Del 8 al 19 inclusive
            suma_base += montos.get(i, Decimal(0))

        # 3. Guardar solo los montos que fueron enviados y son diferentes de 0
        # Si un monto no se envía o es 0, mantener el valor actual
        cambios_detallados = []
        montos_actualizados = False
        for i in range(8, 38):
            monto_field = f'Monto{i:02d}'
            monto_value = montos.get(i, Decimal(0))
            # Solo actualizar si el monto fue enviado y es diferente del actual
            valor_actual = getattr(calificacion, monto_field, Decimal(0))
            if monto_value != valor_actual:
                cambios_detallados.append({
                    'campo': monto_field,
                    'valor_anterior': str(valor_actual),
                    'valor_nuevo': str(monto_value)
                })
                setattr(calificacion, monto_field, monto_value)
                montos_actualizados = True
        
        # Guardar la suma base para poder hacer el cálculo inverso después
        # Solo actualizar si cambió
        suma_base_actual = getattr(calificacion, 'SumaBase', Decimal(0))
        if suma_base != suma_base_actual:
            cambios_detallados.append({
                'campo': 'SumaBase',
                'valor_anterior': str(suma_base_actual),
                'valor_nuevo': str(suma_base)
            })
            calificacion.SumaBase = suma_base
            montos_actualizados = True
        
        # Actualizar la fecha de modificación solo si se actualizaron montos
        if montos_actualizados:
            calificacion.FechaAct = datetime.datetime.now()
            calificacion.save()
            # Guardar log con cambios detallados
            _crear_log(current_user, 'Modificar Calificacion', documento_afectado=calificacion, cambios_detallados=cambios_detallados if cambios_detallados else None)
        
        # 4. Calcular todos los factores (8-37) dividiendo cada monto por la Suma Base
        EIGHT_PLACES = Decimal('0.00000001')
        factores_calculados = {}
        
        if suma_base > 0:
            for i in range(8, 38):
                monto = montos.get(i, Decimal(0))
                factor_calculado = (monto / suma_base).quantize(EIGHT_PLACES)
                factor_field = f'Factor{i:02d}'
                factores_calculados[factor_field] = str(factor_calculado)
        else:
            # Si la suma es 0, todos los factores son 0
            for i in range(8, 38):
                factor_field = f'Factor{i:02d}'
                factores_calculados[factor_field] = '0.00000000'

        # 4. Formatear factores para retornar (sin guardar aún, solo mostrar)
        factores_formateados = {}
        for i in range(8, 38):
            factor_field = f'Factor{i:02d}'
            valor_str = factores_calculados.get(factor_field, '0.00000000')
            # Formatear eliminando ceros innecesarios
            try:
                valor_float = float(valor_str)
                factores_formateados[factor_field] = f"{valor_float:.8f}".rstrip('0').rstrip('.')
                if factores_formateados[factor_field] == '':
                    factores_formateados[factor_field] = '0'
            except (ValueError, TypeError):
                factores_formateados[factor_field] = '0.0'

        # Información de debug
        debug_info = {
            'suma_base': str(suma_base),
        }

        return JsonResponse({
            'success': True,
            'message': 'Factores calculados exitosamente',
            'factores': factores_formateados,
            'suma_base': str(suma_base),
            'debug': debug_info
        })

    except Exception as e:
        print(f"Error al calcular factores: {e}")
        return JsonResponse({'success': False, 'error': f'Error al calcular: {str(e)}'}, status=500)


def administrar_view(request):
    if 'user_id' not in request.session:
        return redirect('login')

    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
    except usuarios.DoesNotExist:
        request.session.flush()
        return redirect('login')

    if not current_user.rol:
        return HttpResponseForbidden("<h1>Acceso Denegado</h1><p>No tienes permisos...</p><a href='/home/'>Volver</a>")

    todos_los_usuarios = usuarios.objects.all()
    return render(request, 'prueba/administrar.html', {
        'user_nombre': current_user.nombre,
        'lista_usuarios': todos_los_usuarios,
        'is_admin': current_user.rol,
        'current_user_id': str(current_user.id)
    })


@require_POST
def crear_usuario_view(request):
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        admin_user = usuarios.objects.get(id=request.session['user_id'])
        if not admin_user.rol:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Admin no válido'}, status=401)

    form = UsuarioForm(request.POST)
    if form.is_valid():
        try:
            # Crear usuario con datos del formulario
            cleaned_data = form.cleaned_data.copy()
            # Eliminar confirmar_contrasena ya que solo es para validación
            cleaned_data.pop('confirmar_contrasena', None)
            # Hashear la contraseña antes de guardar
            if 'contrasena' in cleaned_data and cleaned_data['contrasena']:
                cleaned_data['contrasena'] = _hash_password(cleaned_data['contrasena'])
            
            nuevo_usuario = usuarios(**cleaned_data)
            nuevo_usuario.save()  # Guardar primero para obtener el ID
            
            # Manejar foto de perfil si se proporciona
            if 'foto_perfil' in request.FILES:
                try:
                    foto_ruta = _guardar_foto_perfil(request.FILES['foto_perfil'], str(nuevo_usuario.id))
                    nuevo_usuario.foto_perfil = foto_ruta
                    nuevo_usuario.save()  # Guardar nuevamente con la foto
                except ValueError as e:
                    nuevo_usuario.delete()  # Eliminar usuario si falla la foto
                    return JsonResponse({'success': False, 'error': str(e)}, status=400)
                except Exception as e:
                    nuevo_usuario.delete()  # Eliminar usuario si falla la foto
                    print(f"Error al guardar foto: {e}")
                    return JsonResponse({'success': False, 'error': f'Error al guardar foto: {e}'}, status=500)
            
            _crear_log(admin_user, 'Crear Usuario', usuario_afectado=nuevo_usuario)
            return JsonResponse({'success': True})
        except Exception as e:
            print(f"Error al crear usuario: {e}")
            return JsonResponse({'success': False, 'error': f'Error interno: {e}'}, status=500)
    else:
        return JsonResponse({'success': False, 'error': form.errors.as_json()}, status=400)


@require_POST
def eliminar_usuarios_view(request):
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        admin_user = usuarios.objects.get(id=request.session['user_id'])
        if not admin_user.rol:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Admin no válido'}, status=401)

    try:
        data = json.loads(request.body)
        user_ids_to_delete_str = data.get('user_ids', [])  # Son strings
        if not isinstance(user_ids_to_delete_str, list) or not user_ids_to_delete_str:
            return JsonResponse({'success': False, 'error': 'Lista de IDs inválida'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

    if request.session['user_id'] in user_ids_to_delete_str:
        return JsonResponse({'success': False, 'error': 'No puedes eliminarte a ti mismo'}, status=400)

    try:
        # Convertimos los strings del JSON a ObjectIds para la BBDD
        ids_a_eliminar = [ObjectId(uid) for uid in user_ids_to_delete_str]
    except Exception:
        return JsonResponse({'success': False, 'error': 'Uno o más IDs tienen un formato inválido'}, status=400)

    for user_id in ids_a_eliminar:
        try:
            # Intentamos obtener el usuario antes de eliminarlo para el log y eliminar su foto
            usuario_eliminado = usuarios.objects.get(id=user_id)
            
            # Eliminar foto de perfil si existe
            if usuario_eliminado.foto_perfil:
                try:
                    foto_path = settings.MEDIA_ROOT / usuario_eliminado.foto_perfil
                    if foto_path.exists():
                        foto_path.unlink()
                        print(f"Foto de perfil eliminada: {foto_path}")
                except Exception as e:
                    print(f"Error al eliminar foto de perfil: {e}")
            
            _crear_log(
                admin_user,
                'Eliminar Usuario',
                usuario_afectado=usuario_eliminado
            )
        except usuarios.DoesNotExist: # Si ya no existe, creamos el log con el ID directamente
            _crear_log(
                admin_user,
                'Eliminar Usuario',
                usuario_afectado=user_id
            )
    delete_result = usuarios.objects(id__in=ids_a_eliminar).delete()

    return JsonResponse({'success': True, 'deleted_count': delete_result})


@require_GET
def obtener_usuario_view(request, user_id):
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        admin_user = usuarios.objects.get(id=request.session['user_id'])
        if not admin_user.rol:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Admin no válido'}, status=401)

    try:
        usuario = usuarios.objects.get(id=user_id)
        usuario_data = {
            'id': str(usuario.id),
            'nombre': usuario.nombre,
            'correo': usuario.correo,
            'rol': usuario.rol,
            'foto_perfil': usuario.foto_perfil if usuario.foto_perfil else None
        }
        return JsonResponse({'success': True, 'usuario': usuario_data})
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error interno: {e}'}, status=500)


@require_POST
def modificar_usuario_view(request):
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        admin_user = usuarios.objects.get(id=request.session['user_id'])
        if not admin_user.rol:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Admin no válido'}, status=401)

    # Usar el formulario para validación
    form = UsuarioUpdateForm(request.POST, request.FILES)
    if not form.is_valid():
        # Retornar errores del formulario
        errors_dict = {}
        for field, errors in form.errors.items():
            errors_dict[field] = errors
        return JsonResponse({'success': False, 'error': errors_dict}, status=400)
    
    user_id = form.cleaned_data.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Falta user_id'}, status=400)

    nombre = form.cleaned_data.get('nombre', '').strip()
    correo = form.cleaned_data.get('correo', '').strip()
    contrasena = form.cleaned_data.get('contrasena', '')
    rol = form.cleaned_data.get('rol', False)

    if not nombre or not correo:
        return JsonResponse({'success': False, 'error': 'Nombre y correo son obligatorios.'}, status=400)

    try:
        usuario_a_modificar = usuarios.objects.get(id=user_id)
        usuario_a_modificar.nombre = nombre
        usuario_a_modificar.correo = correo
        # Solo actualizar contraseña si se proporciona (y no está vacía)
        if contrasena and contrasena.strip():
            # Hashear la nueva contraseña antes de guardar
            usuario_a_modificar.contrasena = _hash_password(contrasena)
        usuario_a_modificar.rol = rol
        
        # Manejar foto de perfil si se proporciona
        if 'foto_perfil' in request.FILES:
            try:
                # Eliminar foto anterior si existe
                if usuario_a_modificar.foto_perfil:
                    foto_antigua = settings.MEDIA_ROOT / usuario_a_modificar.foto_perfil
                    if foto_antigua.exists():
                        foto_antigua.unlink()
                
                foto_ruta = _guardar_foto_perfil(request.FILES['foto_perfil'], str(usuario_a_modificar.id))
                usuario_a_modificar.foto_perfil = foto_ruta
            except ValueError as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
            except Exception as e:
                print(f"Error al guardar foto: {e}")
                return JsonResponse({'success': False, 'error': f'Error al guardar foto: {e}'}, status=500)
        
        usuario_a_modificar.save()
        _crear_log(admin_user, 'Modificar Usuario', usuario_afectado=usuario_a_modificar)
        return JsonResponse({'success': True})
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        print("Error interno modificar_usuario_view:", e)
        return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'}, status=500)


def ver_logs_view(request):
    if 'user_id' not in request.session:
        return redirect('login')

    try:
        admin_user = usuarios.objects.get(id=request.session['user_id'])
        if not admin_user.rol:
            return HttpResponseForbidden(
                "<h1>Acceso Denegado</h1>"
                "<p>No tienes permisos de administrador.</p>"
                "<a href='/home/'>Volver</a>"
            )
    except usuarios.DoesNotExist:
        del request.session['user_id']
        del request.session['user_nombre']
        return redirect('login')

    try:
        logs_raw = Log.objects.no_dereference().order_by('-fecharegistrada')
        logs_procesados = []

        for l in logs_raw:
            # --- Actor (usuario que ejecutó la acción) ---
            actor_correo = getattr(l, "correoElectronico", "N/A")
            actor_id = "N/A"
            actor_nombre = "N/A"
            
            if hasattr(l, "Usuarioid") and l.Usuarioid:
                actor_id_obj = _extraer_object_id(l.Usuarioid)
                if actor_id_obj:
                    actor_id = actor_id_obj
                    # Intentar obtener el nombre del actor si aún existe
                    try:
                        actor_usuario = usuarios.objects.get(id=actor_id_obj)
                        actor_nombre = actor_usuario.nombre
                    except usuarios.DoesNotExist:
                        pass  # El usuario ya no existe, mantener N/A

            # --- Usuario o elemento afectado (aunque haya sido eliminado) ---
            afectado_id = "N/A"
            tipo_afectado = "N/A"  # 'Usuario' o 'Calificacion'
            
            if hasattr(l, "usuario_afectado") and l.usuario_afectado:
                afectado_id_obj = _extraer_object_id(l.usuario_afectado)
                if afectado_id_obj:
                    afectado_id = afectado_id_obj
                    tipo_afectado = "Usuario"
            elif hasattr(l, "iddocumento") and l.iddocumento:
                afectado_id_obj = _extraer_object_id(l.iddocumento)
                if afectado_id_obj:
                    afectado_id = afectado_id_obj
                    tipo_afectado = "Calificacion"

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
        print(f"Error al cargar logs: {e}")
        return HttpResponseServerError(
            f"<h1>Error Interno</h1>"
            f"<p>No se pudieron cargar los logs del sistema.</p>"
            f"<p>Error: {e}</p>"
            f"<a href='/home/'>Volver</a>"
        )

    context = {
        "user_nombre": admin_user.nombre,
        "lista_logs": logs_procesados,
    }
    return render(request, "prueba/ver_logs.html", context)


@require_GET
def obtener_calificacion_view(request, calificacion_id):
    """Vista para obtener una calificación por ID"""
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        from decimal import Decimal
        calificacion = Calificacion.objects.get(id=calificacion_id)
        
        # Preparar datos para retornar
        calificacion_data = {
            'id': str(calificacion.id),
            'mercado': calificacion.Mercado or '',
            'origen': calificacion.Origen or '',
            'ejercicio': calificacion.Ejercicio or '',
            'instrumento': calificacion.Instrumento or '',
            'descripcion': calificacion.Descripcion or '',
            'fecha_pago': calificacion.FechaPago.isoformat() if calificacion.FechaPago else '',
            'secuencia_evento': calificacion.SecuenciaEvento or '',
            'dividendo': str(calificacion.Dividendo or 0.0),
            'isfut': calificacion.ISFUT or False,
            'anho': calificacion.Anho or calificacion.Ejercicio or '',
            'valor_historico': str(calificacion.ValorHistorico or 0.0),
            'factor_actualizacion': str(calificacion.FactorActualizacion or 0.0),
            'montos': {},
            'factores': {}
        }
        
        # Obtener la suma base guardada
        suma_base = calificacion.SumaBase or Decimal(0)
        
        # Calcular los montos a partir de los factores guardados (cálculo inverso)
        # monto = factor * suma_base
        for i in range(8, 38):
            factor_field = f'Factor{i:02d}'
            factor_value = getattr(calificacion, factor_field, Decimal(0))
            if suma_base > 0:
                monto_calculado = (factor_value * suma_base).quantize(Decimal('0.01'))
            else:
                monto_calculado = Decimal(0)
            
            monto_field = f'Monto{i:02d}'
            calificacion_data['montos'][monto_field] = str(monto_calculado) if monto_calculado else '0.0'
            
            # También incluir los factores para referencia
            calificacion_data['factores'][factor_field] = str(factor_value) if factor_value else '0.0'
        
        return JsonResponse({
            'success': True,
            'calificacion': calificacion_data
        })
    except Calificacion.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Calificación no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error al obtener calificación: {str(e)}'}, status=500)


@require_POST
def eliminar_calificacion_view(request, calificacion_id):
    """Vista para eliminar una calificación"""
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401)

    try:
        calificacion = Calificacion.objects.get(id=calificacion_id)
        calificacion.delete()
        _crear_log(current_user, 'Eliminar Calificacion', documento_afectado=calificacion)
        return JsonResponse({'success': True, 'message': 'Calificación eliminada exitosamente'})
    except Calificacion.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Calificación no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error al eliminar: {str(e)}'}, status=500)


@require_POST
def copiar_calificacion_view(request, calificacion_id):
    """Vista para copiar una calificación completa con un nuevo ID"""
    print(f"[COPiar] Iniciando copia de calificación ID: {calificacion_id}")
    
    if 'user_id' not in request.session:
        print("[COPiar] Error: No autenticado")
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
        print(f"[COPiar] Usuario autenticado: {current_user.correo}")
    except usuarios.DoesNotExist:
        print("[COPiar] Error: Usuario no válido")
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401)

    try:
        from decimal import Decimal
        
        # Obtener la calificación original
        print(f"[COPiar] Obteniendo calificación original: {calificacion_id}")
        calificacion_original = Calificacion.objects.get(id=calificacion_id)
        print(f"[COPiar] Calificación encontrada: {calificacion_original.Instrumento}")
        
        # Crear una nueva calificación copiando todos los campos
        nueva_calificacion = Calificacion()
        
        # Copiar campos básicos
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
        
        # Copiar todos los factores (Factor08 a Factor37)
        print("[COPiar] Copiando factores...")
        for i in range(8, 38):
            factor_field = f'Factor{i:02d}'
            valor_factor = getattr(calificacion_original, factor_field, Decimal(0))
            setattr(nueva_calificacion, factor_field, valor_factor)
        
        # Copiar todos los montos (Monto08 a Monto37)
        print("[COPiar] Copiando montos...")
        for i in range(8, 38):
            monto_field = f'Monto{i:02d}'
            valor_monto = getattr(calificacion_original, monto_field, Decimal(0))
            setattr(nueva_calificacion, monto_field, valor_monto)
        
        # Copiar SumaBase
        nueva_calificacion.SumaBase = calificacion_original.SumaBase
        
        # FechaAct se establecerá automáticamente al guardar (default=datetime.datetime.now)
        nueva_calificacion.FechaAct = datetime.datetime.now()
        
        # Guardar la nueva calificación
        print("[COPiar] Guardando nueva calificación...")
        nueva_calificacion.save()
        print(f"[COPiar] Nueva calificación guardada con ID: {nueva_calificacion.id}")
        
        # Crear log de la acción
        try:
            _crear_log(current_user, 'Crear Calificacion', documento_afectado=nueva_calificacion)
            print("[COPiar] Log creado exitosamente")
        except Exception as log_error:
            print(f"[COPiar] Advertencia: Error al crear log: {log_error}")
        
        return JsonResponse({
            'success': True,
            'message': 'Calificación copiada exitosamente',
            'nueva_calificacion_id': str(nueva_calificacion.id)
        })
        
    except Calificacion.DoesNotExist:
        print(f"[COPiar] Error: Calificación no encontrada: {calificacion_id}")
        return JsonResponse({'success': False, 'error': 'Calificación no encontrada'}, status=404)
    except Exception as e:
        import traceback
        print(f"[COPiar] Error al copiar calificación: {e}")
        print(f"[COPiar] Traceback: {traceback.format_exc()}")
        return JsonResponse({'success': False, 'error': f'Error al copiar: {str(e)}'}, status=500)


@require_POST
def preview_factor_view(request):
    """Vista para previsualizar archivo CSV con factores"""
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401)

    try:
        import pandas as pd
        from decimal import Decimal
        
        if 'archivo' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No se recibió ningún archivo'}, status=400)
        
        archivo = request.FILES['archivo']
        
        # Leer CSV con pandas
        try:
            # Intentar diferentes encodings
            try:
                df = pd.read_csv(archivo, encoding='utf-8')
            except UnicodeDecodeError:
                archivo.seek(0)
                df = pd.read_csv(archivo, encoding='latin-1')
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al leer el archivo CSV: {str(e)}'}, status=400)
        
        # Limpiar nombres de columnas (eliminar espacios)
        df.columns = df.columns.str.strip()
        
        # Eliminar filas completamente vacías
        df = df.dropna(how='all')
        
        # Convertir a lista de diccionarios
        datos = []
        errores = []
        
        for idx, row in df.iterrows():
            try:
                # Convertir la fila a diccionario
                fila = row.to_dict()
                
                # Convertir valores NaN a strings vacíos y limpiar
                fila_limpia = {}
                for key, value in fila.items():
                    if pd.isna(value):
                        fila_limpia[key] = ''
                    else:
                        fila_limpia[key] = str(value).strip() if value else ''
                
                # Validar campos requeridos (buscar con diferentes variaciones)
                ejercicio = fila_limpia.get('Ejercicio') or fila_limpia.get('ejercicio') or ''
                mercado = fila_limpia.get('Mercado') or fila_limpia.get('mercado') or ''
                
                if not ejercicio or not mercado:
                    errores.append(f'Fila {idx + 2}: Faltan campos requeridos (Ejercicio, Mercado)')
                    continue
                
                datos.append(fila_limpia)
                
            except Exception as e:
                errores.append(f'Fila {idx + 2}: {str(e)}')
                continue
        
        return JsonResponse({
            'success': True,
            'datos': datos,
            'errores': errores,
            'total': len(datos)
        })
        
    except Exception as e:
        print(f"Error al previsualizar factor: {e}")
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': f'Error al procesar: {str(e)}'}, status=500)


@require_POST
def preview_monto_view(request):
    """Vista para previsualizar archivo CSV con montos"""
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401)

    try:
        import pandas as pd
        from decimal import Decimal
        
        if 'archivo' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No se recibió ningún archivo'}, status=400)
        
        archivo = request.FILES['archivo']
        
        # Leer CSV con pandas
        try:
            # Intentar diferentes encodings
            try:
                df = pd.read_csv(archivo, encoding='utf-8')
            except UnicodeDecodeError:
                archivo.seek(0)
                df = pd.read_csv(archivo, encoding='latin-1')
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error al leer el archivo CSV: {str(e)}'}, status=400)
        
        # Limpiar nombres de columnas (eliminar espacios)
        df.columns = df.columns.str.strip()
        
        # Eliminar filas completamente vacías
        df = df.dropna(how='all')
        
        # Convertir a lista de diccionarios
        datos = []
        errores = []
        
        for idx, row in df.iterrows():
            try:
                # Convertir la fila a diccionario
                fila = row.to_dict()
                
                # Convertir valores NaN a strings vacíos y limpiar
                fila_limpia = {}
                for key, value in fila.items():
                    if pd.isna(value):
                        fila_limpia[key] = ''
                    else:
                        fila_limpia[key] = str(value).strip() if value else ''
                
                # Validar campos requeridos (buscar con diferentes variaciones)
                ejercicio = fila_limpia.get('Ejercicio') or fila_limpia.get('ejercicio') or ''
                mercado = fila_limpia.get('Mercado') or fila_limpia.get('mercado') or ''
                
                if not ejercicio or not mercado:
                    errores.append(f'Fila {idx + 2}: Faltan campos requeridos (Ejercicio, Mercado)')
                    continue
                
                datos.append(fila_limpia)
                
            except Exception as e:
                errores.append(f'Fila {idx + 2}: {str(e)}')
                continue
        
        return JsonResponse({
            'success': True,
            'datos': datos,
            'errores': errores,
            'total': len(datos)
        })
        
    except Exception as e:
        print(f"Error al previsualizar monto: {e}")
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': f'Error al procesar: {str(e)}'}, status=500)


@require_POST
def cargar_factor_view(request):
    """Vista para cargar calificaciones desde CSV con factores ya calculados"""
    print("[CARGAR_FACTOR] Iniciando carga de factores...")
    
    if 'user_id' not in request.session:
        print("[CARGAR_FACTOR] Error: No autenticado")
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
        print(f"[CARGAR_FACTOR] Usuario autenticado: {current_user.correo}")
    except usuarios.DoesNotExist:
        print("[CARGAR_FACTOR] Error: Usuario no válido")
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401)

    try:
        import pandas as pd
        import json
        from decimal import Decimal
        
        print("[CARGAR_FACTOR] Parseando JSON...")
        data = json.loads(request.body)
        datos_csv = data.get('datos', [])
        
        print(f"[CARGAR_FACTOR] Datos recibidos: {len(datos_csv)} filas")
        
        if not datos_csv:
            print("[CARGAR_FACTOR] Error: No se recibieron datos")
            return JsonResponse({'success': False, 'error': 'No se recibieron datos'}, status=400)
        
        # Convertir a DataFrame de pandas para procesamiento más eficiente
        df = pd.DataFrame(datos_csv)
        
        # Limpiar nombres de columnas (eliminar espacios)
        df.columns = df.columns.str.strip()
        
        # Eliminar filas completamente vacías
        df = df.dropna(how='all')
        
        calificaciones_creadas = 0
        errores = []
        
        # Iterar sobre el DataFrame
        for idx, row in df.iterrows():
            fila_num = idx + 2  # +2 porque idx empieza en 0 y la fila 1 es el encabezado
            try:
                # Convertir la fila a diccionario
                fila = row.to_dict()
                
                # Convertir valores NaN a strings vacíos y limpiar
                fila_limpia = {}
                for key, value in fila.items():
                    if pd.isna(value):
                        fila_limpia[key] = ''
                    else:
                        fila_limpia[key] = str(value).strip() if value else ''
                
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
                if mercado_raw:
                    mercado_lower = mercado_raw.lower().strip()
                    if mercado_lower == 'acciones' or mercado_lower == 'accion':
                        mercado_normalizado = 'acciones'
                    elif mercado_lower == 'cfi':
                        mercado_normalizado = 'CFI'
                    elif mercado_lower == 'fondos mutuos' or mercado_lower == 'fondosmutuos' or mercado_lower == 'fondo mutuo':
                        mercado_normalizado = 'Fondos mutuos'
                
                mercado = mercado_normalizado
                
                # Detectar si Ejercicio e Instrumento están intercambiados
                # Si Ejercicio contiene letras (como "ACC001") e Instrumento es numérico, intercambiar
                ejercicio_es_numero = False
                instrumento_es_numero = False
                ejercicio_tiene_letras = any(c.isalpha() for c in str(ejercicio)) if ejercicio else False
                
                try:
                    int(ejercicio)
                    ejercicio_es_numero = True
                except (ValueError, TypeError):
                    pass
                
                try:
                    int(instrumento)
                    instrumento_es_numero = True
                except (ValueError, TypeError):
                    pass
                
                # Si Ejercicio no es numérico pero Instrumento sí, intercambiar
                # O si Ejercicio tiene letras (parece código de instrumento) e Instrumento es numérico (parece año)
                if (not ejercicio_es_numero and instrumento_es_numero) or (ejercicio_tiene_letras and instrumento_es_numero):
                    print(f"[CARGAR_FACTOR] Advertencia: Ejercicio e Instrumento parecen estar intercambiados en fila {idx}. Ejercicio: '{ejercicio}', Instrumento: '{instrumento}'")
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
                nueva_calificacion.Descripcion = fila_limpia.get('DESCRIPCION') or fila_limpia.get('Descripcion') or fila_limpia.get('descripcion') or ''
                
                # Fecha de pago usando pandas
                fecha_pago = fila_limpia.get('FEC_PAGO') or fila_limpia.get('Fec_Pago') or fila_limpia.get('fec_pago') or ''
                if fecha_pago:
                    try:
                        fecha_parsed = pd.to_datetime(fecha_pago, format='%Y-%m-%d', errors='coerce')
                        if not pd.isna(fecha_parsed):
                            nueva_calificacion.FechaPago = fecha_parsed.to_pydatetime()
                    except Exception as e:
                        print(f"[CARGAR_FACTOR] Error al parsear fecha: {e}")
                        pass
                
                # Secuencia evento usando pandas
                sec_eve = fila_limpia.get('SEC_EVE') or fila_limpia.get('Sec_Eve') or fila_limpia.get('sec_eve') or ''
                if sec_eve:
                    try:
                        nueva_calificacion.SecuenciaEvento = pd.to_numeric(sec_eve, errors='raise').astype(int)
                    except (ValueError, TypeError, Exception):
                        print(f"[CARGAR_FACTOR] Advertencia: No se pudo convertir SecuenciaEvento '{sec_eve}' a entero en fila {fila_num}")
                        pass
                
                # Asignar factores (F8 a F37) usando pandas
                for i in range(8, 38):
                    factor_key = f'F{i}'
                    factor_value = fila_limpia.get(factor_key, '0.0')
                    try:
                        # Usar pandas para convertir a numérico
                        factor_numeric = pd.to_numeric(factor_value, errors='coerce')
                        if pd.isna(factor_numeric):
                            factor_decimal = Decimal(0)
                        else:
                            factor_decimal = Decimal(str(factor_numeric))
                            # Validar que el factor esté entre 0 y 1
                            if factor_decimal < 0:
                                factor_decimal = Decimal(0)
                            elif factor_decimal > 1:
                                factor_decimal = Decimal(1)
                        setattr(nueva_calificacion, f'Factor{i:02d}', factor_decimal)
                    except Exception as e:
                        print(f"[CARGAR_FACTOR] Error al procesar factor {i}: {e}")
                        setattr(nueva_calificacion, f'Factor{i:02d}', Decimal(0))
                
                nueva_calificacion.FechaAct = datetime.datetime.now()
                nueva_calificacion.save()
                calificaciones_creadas += 1
                print(f"[CARGAR_FACTOR] Calificación {fila_num} guardada exitosamente")
                
            except Exception as e:
                print(f"[CARGAR_FACTOR] Error en fila {fila_num}: {e}")
                import traceback
                print(traceback.format_exc())
                errores.append(f'Fila {fila_num}: {str(e)}')
                continue
        
        # Crear log de carga masiva
        if calificaciones_creadas > 0:
            _crear_log(current_user, 'Carga Masiva', documento_afectado=None)
            print(f"[CARGAR_FACTOR] Log creado para {calificaciones_creadas} calificaciones")
        
        mensaje = f'Se crearon {calificaciones_creadas} calificación(es) exitosamente.'
        if errores:
            mensaje += f' Se encontraron {len(errores)} error(es).'
        
        print(f"[CARGAR_FACTOR] Proceso completado: {calificaciones_creadas} creadas, {len(errores)} errores")
        
        return JsonResponse({
            'success': True,
            'total': calificaciones_creadas,
            'errores': errores,
            'message': mensaje
        })
        
    except Exception as e:
        print(f"[CARGAR_FACTOR] Error al cargar factores: {e}")
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': f'Error al procesar: {str(e)}'}, status=500)


@require_POST
def cargar_monto_view(request):
    """Vista para cargar calificaciones desde CSV con montos (factores ya calculados)"""
    print("[CARGAR_MONTO] Iniciando carga de montos...")
    
    if 'user_id' not in request.session:
        print("[CARGAR_MONTO] Error: No autenticado")
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        current_user = usuarios.objects.get(id=request.session['user_id'])
        print(f"[CARGAR_MONTO] Usuario autenticado: {current_user.correo}")
    except usuarios.DoesNotExist:
        print("[CARGAR_MONTO] Error: Usuario no válido")
        return JsonResponse({'success': False, 'error': 'Usuario no válido'}, status=401)

    try:
        import pandas as pd
        import json
        from decimal import Decimal
        
        print("[CARGAR_MONTO] Parseando JSON...")
        data = json.loads(request.body)
        datos_csv = data.get('datos', [])
        
        print(f"[CARGAR_MONTO] Datos recibidos: {len(datos_csv)} filas")
        
        if not datos_csv:
            print("[CARGAR_MONTO] Error: No se recibieron datos")
            return JsonResponse({'success': False, 'error': 'No se recibieron datos'}, status=400)
        
        # Convertir a DataFrame de pandas para procesamiento más eficiente
        df = pd.DataFrame(datos_csv)
        
        # Limpiar nombres de columnas (eliminar espacios)
        df.columns = df.columns.str.strip()
        
        # Eliminar filas completamente vacías
        df = df.dropna(how='all')
        
        calificaciones_creadas = 0
        errores = []
        
        # Iterar sobre el DataFrame
        for idx, row in df.iterrows():
            fila_num = idx + 2  # +2 porque idx empieza en 0 y la fila 1 es el encabezado
            try:
                # Convertir la fila a diccionario
                fila = row.to_dict()
                
                # Convertir valores NaN a strings vacíos y limpiar
                fila_limpia = {}
                for key, value in fila.items():
                    if pd.isna(value):
                        fila_limpia[key] = ''
                    else:
                        fila_limpia[key] = str(value).strip() if value else ''
                
                # Debug: mostrar las claves disponibles en la primera fila
                if fila_num == 2:
                    print(f"[CARGAR_MONTO] Claves disponibles en CSV: {list(fila_limpia.keys())}")
                    print(f"[CARGAR_MONTO] Primera fila completa: {fila_limpia}")
                    print(f"[CARGAR_MONTO] Ejercicio raw: '{fila_limpia.get('Ejercicio')}'")
                    print(f"[CARGAR_MONTO] Mercado raw: '{fila_limpia.get('Mercado')}'")
                    print(f"[CARGAR_MONTO] Instrumento raw: '{fila_limpia.get('Instrumento')}'")
                
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
                
                mercado = mercado_normalizado
                
                # Detectar si Ejercicio e Instrumento están intercambiados
                # Si Ejercicio contiene letras (como "ACC001") e Instrumento es numérico, intercambiar
                ejercicio_es_numero = False
                instrumento_es_numero = False
                ejercicio_tiene_letras = any(c.isalpha() for c in str(ejercicio)) if ejercicio else False
                
                try:
                    int(ejercicio)
                    ejercicio_es_numero = True
                except (ValueError, TypeError):
                    pass
                
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
                tiene_factores = any(f'F{i}' in fila_limpia for i in range(8, 38))
                
                if tiene_factores:
                    # Los factores ya están calculados, solo asignarlos usando pandas
                    for i in range(8, 38):
                        factor_key = f'F{i}'
                        factor_value = fila_limpia.get(factor_key, '0.0')
                        try:
                            factor_numeric = pd.to_numeric(factor_value, errors='coerce')
                            if pd.isna(factor_numeric):
                                factor_decimal = Decimal(0)
                            else:
                                factor_decimal = Decimal(str(factor_numeric))
                                if factor_decimal < 0:
                                    factor_decimal = Decimal(0)
                                elif factor_decimal > 1:
                                    factor_decimal = Decimal(1)
                            setattr(nueva_calificacion, f'Factor{i:02d}', factor_decimal)
                        except Exception as e:
                            print(f"[CARGAR_MONTO] Error al procesar factor {i}: {e}")
                            setattr(nueva_calificacion, f'Factor{i:02d}', Decimal(0))
                    
                    # Si hay montos originales, guardarlos también usando pandas
                    suma_base = Decimal(0)
                    for i in range(8, 38):
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
                            setattr(nueva_calificacion, f'Monto{i:02d}', monto_decimal)
                            if i <= 19:
                                suma_base += monto_decimal
                        except Exception as e:
                            print(f"[CARGAR_MONTO] Error al procesar monto {i}: {e}")
                            setattr(nueva_calificacion, f'Monto{i:02d}', Decimal(0))
                    
                    nueva_calificacion.SumaBase = suma_base
                else:
                    # Obtener montos y calcular suma base usando pandas
                    montos = []
                    suma_base = Decimal(0)
                    
                    for i in range(8, 38):
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
                    
                    nueva_calificacion.SumaBase = suma_base
                    
                    # Guardar montos
                    for i in range(8, 38):
                        setattr(nueva_calificacion, f'Monto{i:02d}', montos[i - 8])
                    
                    # Calcular factores
                    if suma_base > 0:
                        EIGHT_PLACES = Decimal('0.00000001')
                        for i in range(8, 38):
                            factor = (montos[i - 8] / suma_base).quantize(EIGHT_PLACES)
                            if factor > 1:
                                factor = Decimal(1)
                            setattr(nueva_calificacion, f'Factor{i:02d}', factor)
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
        
        # Crear log de carga masiva
        if calificaciones_creadas > 0:
            _crear_log(current_user, 'Carga Masiva', documento_afectado=None)
            print(f"[CARGAR_MONTO] Log creado para {calificaciones_creadas} calificaciones")
        
        mensaje = f'Se crearon {calificaciones_creadas} calificación(es) exitosamente.'
        if errores:
            mensaje += f' Se encontraron {len(errores)} error(es).'
        
        print(f"[CARGAR_MONTO] Proceso completado: {calificaciones_creadas} creadas, {len(errores)} errores")
        
        return JsonResponse({
            'success': True,
            'total': calificaciones_creadas,
            'errores': errores,
            'message': mensaje
        })
        
    except Exception as e:
        print(f"[CARGAR_MONTO] Error al cargar montos: {e}")
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': f'Error al procesar: {str(e)}'}, status=500)


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