from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, JsonResponse, Http404
import json
from django.views.decorators.http import require_POST, require_GET
from .formulario import LoginForm, CalificacionModalForm, UsuarioForm, UsuarioUpdateForm
from .models import usuarios, Calificacion # importamos la clase usuarios de models para trabajar onda aca rescatamos los datos del documento los cuales usaremos para trabajar

def listar_usuarios(request):
    #Hacemos la consulta a MongoDB usando el modelo rescatado de models
    todos_los_usuarios = usuarios.objects.all()

    # Preparamos el contexto. 
    context = {
        'usuarios': todos_los_usuarios 
    }
    #lo llevamos al html
    return render(request, 'prueba/listar.html', context)


def login_view(request): #esto es para el login
    if 'user_id' in request.session:
        return redirect('home')
    form = LoginForm()
    error = None
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            # Obtenemos el correo
            correo_usuario = form.cleaned_data['correo'] 
            contrasena_usuario = form.cleaned_data['contrasena']
            try:
                # Buscamos al usuario en MongoDB por su correo
                user = usuarios.objects.get(
                    correo=correo_usuario, 
                    contrasena=contrasena_usuario
                )
            except usuarios.DoesNotExist:
                user = None
            if user:
                # Guardamos la sesión
                request.session['user_id'] = str(user.id)
                request.session['user_nombre'] = user.nombre # Usamos el nombre para saludar
                
                return redirect('home')
            else:
                error = "Correo o contraseña incorrectos."  
    return render(request, 'prueba/login.html', {'form': form, 'error': error})


def home_view(request):
    """
    Muestra el Dashboard principal.
    ¡ACTUALIZADO! Ahora también pasa el rol del usuario ('is_admin').
    """
    if 'user_id' not in request.session:
        return redirect('login')

    user_id = request.session['user_id']
    is_admin = False # Valor por defecto: no es admin
    try:
        # Buscamos al usuario en MongoDB para obtener su rol
        current_user = usuarios.objects.get(id=user_id)
        if current_user.rol == True:
            is_admin = True # Si tiene rol=True, lo marcamos
    except usuarios.DoesNotExist:
        # Si el usuario no existe (raro), lo deslogueamos
        try:
            del request.session['user_id']
            del request.session['user_nombre']
        except KeyError: pass
        return redirect('login')

    # Pasamos el nombre Y si es admin (True/False) a la plantilla
    context = {
        'user_nombre': request.session.get('user_nombre'),
        'is_admin': is_admin 
    }
    return render(request, 'prueba/home.html', context)


def logout_view(request): #pagina para cerrar la sesion xd
    try:
        del request.session['user_id']
        del request.session['user_nombre']
    except KeyError:
        pass

    return redirect('login')


def ingresar_view(request):
    """
    ¡CORREGIDO!
    Ahora lee los datos del modal (incluyendo 'Mercado')
    desde la URL (request.GET) y los pone como
    valores iniciales en el formulario.
    """
    if 'user_id' not in request.session:
        return redirect('login')
    
    if request.method == 'POST':
        form = CalificacionModalForm(request.POST)
        if form.is_valid():
            nueva_calificacion = Calificacion(**form.cleaned_data)
            nueva_calificacion.save()
            return redirect('home')
    else:
        # --- ¡CAMBIO GRANDE AQUÍ! ---
        # 1. Leemos todos los datos que vienen del modal por la URL
        initial_data = {
            'Mercado': request.GET.get('mercado', None),
            'Ejercicio': request.GET.get('ejercicio', None),
            'Instrumento': request.GET.get('instrumento', None),
            'FechaPago': request.GET.get('fecha_pago', None),
            'SecuenciaEvento': request.GET.get('secuencia', None),
        }
        
        # 2. Creamos el formulario con esos valores iniciales
        form = CalificacionModalForm(initial=initial_data)
        # --- FIN DEL CAMBIO ---

    return render(request, 'prueba/ingresar.html', {'form': form})

def administrar_view(request):
    """
    Vista para la página de ADMINISTRACIÓN DE USUARIOS.
    Solo accesible si el usuario tiene rol=True.
    ¡ACTUALIZADO! Ahora obtiene y muestra todos los usuarios.
    """
    # 1. Verificar si está logueado
    if 'user_id' not in request.session:
        return redirect('login')

    user_id = request.session['user_id']
    
    try:
        current_user = usuarios.objects.get(id=user_id)
        
        # 2. Verificar si es admin
        if current_user.rol == True:
            
            # --- ¡CAMBIO AQUÍ! ---
            # 3. Obtenemos TODOS los usuarios de MongoDB
            todos_los_usuarios = usuarios.objects.all()
            
            # 4. Los pasamos al contexto junto con el nombre del admin
            context = {
                'user_nombre': request.session.get('user_nombre'),
                'lista_usuarios': todos_los_usuarios # Pasamos la lista a la plantilla
            }
            # --- FIN DEL CAMBIO ---
            
            # Mostramos la plantilla de administración de usuarios
            return render(request, 'prueba/administrar.html', context)
        else:
            # Si NO es admin, acceso denegado
            return HttpResponseForbidden("<h1>Acceso Denegado</h1><p>No tienes permisos de administrador para ver esta página.</p><a href='/home/'>Volver al inicio</a>")

    except usuarios.DoesNotExist:
        # Si el usuario de la sesión no existe, limpiamos y al login
        try:
            del request.session['user_id']
            del request.session['user_nombre']
        except KeyError: pass
        return redirect('login')

@require_POST 
def crear_usuario_view(request):
    # ... (verificación de admin - asegúrate que devuelva JsonResponse en error) ...
    if 'user_id' not in request.session: return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)
    try: # ... chequeo de rol ...
        admin_user = usuarios.objects.get(id=request.session['user_id'])
        if not admin_user.rol: return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    except usuarios.DoesNotExist: return JsonResponse({'success': False, 'error': 'Admin no válido'}, status=401)

    form = UsuarioForm(request.POST)
    if form.is_valid():
        try:
            nuevo_usuario = usuarios(
                nombre=form.cleaned_data['nombre'],
                correo=form.cleaned_data['correo'],
                contrasena=form.cleaned_data['contrasena'], # ¡HASHEAR!
                rol=form.cleaned_data['rol']
            )
            nuevo_usuario.save() 
            # --- ¡RESPUESTA CORRECTA! ---
            return JsonResponse({'success': True}) 
        except Exception as e:
            print(f"Error al crear usuario: {e}") # Log para el servidor
            # --- ¡RESPUESTA CORRECTA EN ERROR! ---
            return JsonResponse({'success': False, 'error': f'Error interno al guardar: {e}'}, status=500) 
    else:
        # --- ¡RESPUESTA CORRECTA EN VALIDACIÓN! ---
        print("Errores de formulario (Crear):", form.errors.as_json()) # Log para el servidor
        return JsonResponse({'success': False, 'error': form.errors.as_json()}, status=400) 

@require_POST 
def eliminar_usuarios_view(request):
    # ... (verificación de admin - asegúrate que devuelva JsonResponse en error) ...
    if 'user_id' not in request.session: return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)
    try: # ... chequeo de rol ...
        admin_user = usuarios.objects.get(id=request.session['user_id'])
        if not admin_user.rol: return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    except usuarios.DoesNotExist: return JsonResponse({'success': False, 'error': 'Admin no válido'}, status=401)

    # ... (leer user_ids del JSON) ...
    try:
        data = json.loads(request.body)
        user_ids_to_delete = data.get('user_ids', [])
        if not isinstance(user_ids_to_delete, list) or not user_ids_to_delete:
             return JsonResponse({'success': False, 'error': 'Lista de IDs inválida'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

    try:
        # ... (verificar no autoeliminarse) ...
        if request.session['user_id'] in user_ids_to_delete:
             return JsonResponse({'success': False, 'error': 'No puedes eliminarte a ti mismo'}, status=400)

        delete_result = usuarios.objects(id__in=user_ids_to_delete).delete() 
        print(f"Usuarios eliminados: {delete_result}") # Log para el servidor
        
        # --- ¡RESPUESTA CORRECTA! ---
        return JsonResponse({'success': True, 'deleted_count': delete_result}) 
        
    except Exception as e:
        print(f"Error al eliminar usuarios: {e}") # Log para el servidor
        # --- ¡RESPUESTA CORRECTA EN ERROR! ---
        return JsonResponse({'success': False, 'error': f'Error interno al eliminar: {e}'}, status=500) 

# ... (obtener_usuario_view y modificar_usuario_view - asegúrate que devuelvan JSON en todos los casos) ...
@require_GET
def obtener_usuario_view(request, user_id):
     # ... (verificación admin con JsonResponse) ...
     try:
         usuario = usuarios.objects.get(id=user_id)
         usuario_data = { # ... datos ...
            'id': str(usuario.id), 'nombre': usuario.nombre, 'correo': usuario.correo, 'rol': usuario.rol
         }
         return JsonResponse({'success': True, 'usuario': usuario_data})
     except usuarios.DoesNotExist:
         return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404)
     except Exception as e:
         return JsonResponse({'success': False, 'error': f'Error interno: {e}'}, status=500)

@require_POST
def modificar_usuario_view(request):
    # Autenticación/permiso
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)
    try:
        admin_user = usuarios.objects.get(id=request.session['user_id'])
        if not admin_user.rol:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Admin no válido'}, status=401)

    # VALIDACIÓN SIMPLE (puedes seguir usando UsuarioUpdateForm si prefieres)
    user_id = request.POST.get('user_id') or request.POST.get('id')  # aceptación por si hay nombre distinto
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Falta user_id en la petición'}, status=400)

    nombre = request.POST.get('nombre', '').strip()
    correo = request.POST.get('correo', '').strip()
    contrasena = request.POST.get('contrasena', '')  # nombre del campo según tu formulario -> 'contrasena'
    rol_raw = request.POST.get('rol', 'false')

    # Normalizar rol (acepta 'true', 'True', 'on', '1', True)
    rol = str(rol_raw).lower() in ('true', '1', 'on', 'yes')

    if not nombre or not correo:
        return JsonResponse({'success': False, 'error': 'Nombre y correo son obligatorios.'}, status=400)

    try:
        usuario = usuarios.objects.get(id=user_id)
        usuario.nombre = nombre
        usuario.correo = correo

        # Solo actualizar contraseña si se entregó una no vacía
        if contrasena:
            # idealmente hashear la contraseña aquí (bcrypt u otra)
            usuario.contrasena = contrasena

        usuario.rol = rol
        usuario.save()
        return JsonResponse({'success': True})
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        # LOG para servidor
        print("Error interno modificar_usuario_view:", e)
        return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'}, status=500)