import json  # Para manejar datos JSON en las respuestas de API (crear_usuario_view, eliminar_usuarios_view, etc.)
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
from .formulario import LoginForm, CalificacionModalForm, UsuarioForm, FactoresForm, MontosForm  # Formularios Django para validación de datos
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


#Función para crear logs
def _crear_log(usuario_obj, accion_str, documento_afectado=None, usuario_afectado=None):#Guarda un registro de log con información sobre la acción realizada.
    try:
        nuevo_log = Log(
            Usuarioid=usuario_obj,
            correoElectronico=usuario_obj.correo,
            accion=accion_str,
            iddocumento=documento_afectado,
            usuario_afectado=usuario_afectado
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
                user = usuarios.objects.get(correo=correo_usuario, contrasena=contrasena_usuario)
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

    # Obtener calificaciones si hay filtros
    calificaciones = []
    if request.method == 'GET':
        mercado = request.GET.get('mercado', '')
        origen = request.GET.get('origen', '')
        periodo = request.GET.get('periodo', '')
        
        if mercado or origen or periodo:
            query = {}
            if mercado:
                query['Mercado'] = mercado
            if origen:
                query['Origen'] = origen
            if periodo:
                try:
                    periodo_int = int(periodo)
                    query['Ejercicio'] = periodo_int
                except ValueError:
                    pass
            
            calificaciones = Calificacion.objects(**query).order_by('-FechaAct')

    return render(request, 'prueba/home.html', {
        'user_nombre': current_user.nombre,
        'is_admin': is_admin,
        'current_user': current_user,
        'calificaciones': calificaciones
    })


@require_GET
def buscar_calificaciones_view(request):
    """Vista para buscar calificaciones según filtros de mercado, origen y periodo"""
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    try:
        mercado = request.GET.get('mercado', '').strip()
        origen = request.GET.get('origen', '').strip()
        periodo = request.GET.get('periodo', '').strip()

        # Construir query de filtrado
        query = {}
        if mercado:
            query['Mercado'] = mercado
        if origen:
            query['Origen'] = origen
        if periodo:
            try:
                periodo_int = int(periodo)
                query['Ejercicio'] = periodo_int
            except ValueError:
                pass

        # Buscar calificaciones
        calificaciones = Calificacion.objects(**query).order_by('-FechaAct')

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
            
            # Verificar si es una actualización o creación
            calificacion_id = request.POST.get('calificacion_id')
            if calificacion_id:
                # Actualizar calificación existente
                try:
                    calificacion = Calificacion.objects.get(id=calificacion_id)
                    # Actualizar campos
                    for key, value in cleaned_data.items():
                        setattr(calificacion, key, value)
                    calificacion.FechaAct = datetime.datetime.now()  # Actualizar fecha de modificación
                    calificacion.save()
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
                nueva_calificacion.Mercado = form.cleaned_data.get('Mercado', '')
                nueva_calificacion.Instrumento = form.cleaned_data.get('Instrumento', '')
                nueva_calificacion.Origen = form.cleaned_data.get('Origen', 'MANUAL')
                
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
        # Actualizar todos los factores en la calificación desde el POST
        for i in range(8, 38):
            factor_field = f'Factor{i:02d}'
            valor_post = request.POST.get(factor_field, '0.0')
            try:
                valor_decimal = Decimal(str(valor_post)) if valor_post else Decimal(0)
                setattr(calificacion, factor_field, valor_decimal)
            except (ValueError, TypeError):
                setattr(calificacion, factor_field, Decimal(0))
        
        calificacion.save()
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

        # 3. Calcular todos los factores (8-37) dividiendo cada monto por la Suma Base
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
            nuevo_usuario = usuarios(**form.cleaned_data)
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

    user_id = request.POST.get('user_id') or request.POST.get('id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Falta user_id'}, status=400)

    nombre = request.POST.get('nombre', '').strip()
    correo = request.POST.get('correo', '').strip()
    contrasena = request.POST.get('contrasena', '')
    rol_raw = request.POST.get('rol', 'false')
    rol = str(rol_raw).lower() in ('true', '1', 'on', 'yes')

    if not nombre or not correo:
        return JsonResponse({'success': False, 'error': 'Nombre y correo son obligatorios.'}, status=400)

    try:
        usuario_a_modificar = usuarios.objects.get(id=user_id)
        usuario_a_modificar.nombre = nombre
        usuario_a_modificar.correo = correo
        if contrasena:
            usuario_a_modificar.contrasena = contrasena
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
        }
        
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