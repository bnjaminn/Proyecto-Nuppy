import json  # Para manejar datos JSON en las respuestas de API (crear_usuario_view, eliminar_usuarios_view, etc.)
import re  # Para expresiones regulares - usado en _extraer_object_id() para parsear DBRef y extraer ObjectIds
import os  # Para operaciones del sistema de archivos usado en _guardar_foto_perfil() para manejar rutas y extensiones
from django.shortcuts import render, redirect  # render: renderizar templates HTML | redirect: redirigir a otras URLs
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseServerError  # Respuestas HTTP: Forbidden(403), JSON, ServerError(500)
from django.views.decorators.http import require_POST, require_GET  # Decoradores para restringir métodos HTTP (POST/GET)
from django.conf import settings  # Acceso a configuración de Django usado en _guardar_foto_perfil() para MEDIA_ROOT
from mongoengine.errors import DoesNotExist  # Excepción cuando un documento no existe en MongoDB
from bson import ObjectId  # Tipo ObjectId de MongoDB - usado en _extraer_object_id() y operaciones con IDs
try:
    from PIL import Image  # librería para procesamiento de imágenes - usado en _guardar_foto_perfil() para redimensionar fotos
    HAS_PIL = True
except ImportError:
    HAS_PIL = False  # Si no está instalado Pillow, las imágenes no se redimensionarán pero la app funcionará
from .formulario import LoginForm, CalificacionModalForm, UsuarioForm, FactoresForm  # Formularios Django para validación de datos
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

    return render(request, 'prueba/home.html', {
        'user_nombre': current_user.nombre,
        'is_admin': is_admin,
        'current_user': current_user
    })


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
            
            nueva_calificacion = Calificacion(**cleaned_data)
            nueva_calificacion.save()
            _crear_log(current_user, 'Crear Calificacion', documento_afectado=nueva_calificacion)
            # Retornar JSON con el ID de la calificación para abrir el segundo modal
            return JsonResponse({
                'success': True,
                'calificacion_id': str(nueva_calificacion.id),
                'data': {
                    'mercado': nueva_calificacion.Mercado or '',
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


@require_POST
def guardar_factores_view(request):
    """Vista para guardar los factores después de completar los datos básicos"""
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

    # Crear formulario con los factores
    form = FactoresForm(request.POST)
    if form.is_valid():
        # Actualizar todos los factores en la calificación
        for i in range(8, 38):  # Del 8 al 37
            field_name = f'Factor{i:02d}'
            if field_name in form.cleaned_data:
                setattr(calificacion, field_name, form.cleaned_data[field_name] or 0.0)
        
        # Actualizar campos adicionales según mockup
        if 'RentasExentas' in form.cleaned_data:
            calificacion.RentasExentas = form.cleaned_data['RentasExentas'] or 0.0
        if 'Factor19A' in form.cleaned_data:
            calificacion.Factor19A = form.cleaned_data['Factor19A'] or 0.0
        
        calificacion.save()
        _crear_log(current_user, 'Modificar Calificacion', documento_afectado=calificacion)
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': form.errors.as_json()}, status=400)


@require_POST
def calcular_factores_view(request):
    """Vista para calcular factores (placeholder - implementar lógica de cálculo)"""
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)

    # TODO: Implementar lógica de cálculo según los requisitos del negocio
    # Por ahora solo retorna éxito
    return JsonResponse({'success': True, 'message': 'Cálculo realizado (función pendiente de implementar)'})


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