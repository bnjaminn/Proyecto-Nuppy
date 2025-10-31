import json
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_POST, require_GET
from mongoengine.errors import DoesNotExist
from bson import ObjectId

from .formulario import LoginForm, CalificacionModalForm, UsuarioForm
from .models import usuarios, Calificacion, Log


# --- Función Auxiliar para crear logs ---
def _crear_log(usuario_obj, accion_str, documento_afectado=None, usuario_afectado=None):
    """
    Guarda un registro de log con información sobre la acción realizada.
    """
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
        'is_admin': is_admin
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
            nueva_calificacion = Calificacion(**form.cleaned_data)
            nueva_calificacion.save()
            _crear_log(current_user, 'Crear Calificacion', documento_afectado=nueva_calificacion)
            return redirect('home')
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
        'is_admin': current_user.rol
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
            nuevo_usuario = usuarios(**form.cleaned_data)
            nuevo_usuario.save()
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

    # --- INICIA CORRECCIÓN ---
    # 1. Iterar y guardar un log por CADA usuario a eliminar
    # Hacemos esto ANTES de borrarlos.
    for user_id in ids_a_eliminar:
        _crear_log(
            admin_user,
            'Eliminar Usuario',
            usuario_afectado=user_id  # <--- Pasamos el ObjectId del afectado
        )

    # 2. Ahora sí, eliminar todos los usuarios de golpe
    delete_result = usuarios.objects(id__in=ids_a_eliminar).delete()
    # --- FIN CORRECCIÓN ---

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
            'rol': usuario.rol
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
            # --- Actor (usuario que ejecutó la acción)
            actor_correo = getattr(l, "correoElectronico", "N/A")
            actor_id = "N/A"  # Default
            if hasattr(l, "Usuarioid") and l.Usuarioid:
                try:
                    # Simplificado: l.Usuarioid ES el ID
                    actor_id = str(l.Usuarioid)
                except Exception:
                    actor_id = "Desconocido"

            # --- Usuario o elemento afectado (aunque haya sido eliminado)
            afectado_id = "N/A"  # Default
            if hasattr(l, "usuario_afectado") and l.usuario_afectado:
                try:
                    # Simplificado: l.usuario_afectado ES el ID
                    afectado_id = str(l.usuario_afectado)
                except Exception:
                    afectado_id = "Desconocido (err1)"
            elif hasattr(l, "iddocumento") and l.iddocumento:
                try:
                    # Simplificado: l.iddocumento ES el ID
                    afectado_id = str(l.iddocumento)
                except Exception:
                    afectado_id = "Desconocido (err2)"

            logs_procesados.append({
                "fecha": getattr(l, "fecharegistrada", None),
                "actor_correo": actor_correo,
                "actor_id": actor_id,
                "accion": getattr(l, "accion", "N/A"),
                "afectado_id": afectado_id,
            })

    except Exception as e:
        return HttpResponseForbidden(f"Error interno al cargar logs: {e}")

    context = {
        "user_nombre": admin_user.nombre,
        "lista_logs": logs_procesados,
    }
    return render(request, "prueba/ver_logs.html", context)