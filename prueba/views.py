from django.shortcuts import render, redirect, get_object_or_404 #Funciones de Django
from django.http import HttpResponseForbidden, JsonResponse, Http404 # JsonResponse: para enviar respuestas a JavaScript (AJAX), HttpResponseForbidden: para mostrar error de "Acceso Denegado",  Http404: para errores "No encontrado"
import json # Para leer datos enviados como JSON
from django.views.decorators.http import require_POST, require_GET #para restringir métodos HTTP (POST o GET)
from .formulario import LoginForm, CalificacionModalForm, UsuarioForm, UsuarioUpdateForm # Importa los formularios definidos en formulario.py
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


def login_view(request): #Funcion/vista para el login
    if 'user_id' in request.session: #Revisamos si en la sesion el user_id existe
        return redirect('home') #Si existe lo llevamos directo al dashboard
    form = LoginForm() #Mandamos el formulario del login vacío y sin error para la primera carga con esto usamos el GET
    error = None
    if request.method == 'POST': #se empieza un if para ver si el usuario envio el formulario
        form = LoginForm(request.POST) #Crea el formulario con los datos enviados por eso el POST
        if form.is_valid(): #aca se verifica que el formato de los datos sean correctos 
            # Obtenemos el correo y contra
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
                # Esto pasa solo si se encuentra con exito al usuario y Guardamos la sesión
                request.session['user_id'] = str(user.id)
                request.session['user_nombre'] = user.nombre # Usamos el nombre para saludar
                
                return redirect('home') #aca dirige al dashboard si el login fue con exito
            else: # Si no lo encontró, prepara mensaje de error
                error = "Correo o contraseña incorrectos."  
    return render(request, 'prueba/login.html', {'form': form, 'error': error}) #Muestra la plantilla del login.html, pasándole el formulario (vacío) y el mensaje de error si es que existe





def home_view(request): #Funcion/vista para el dashboard
    if 'user_id' not in request.session: #verifica que este el usuario logeado de no ser asi te manda devuelta al login
        return redirect('login')
    user_id = request.session['user_id'] #Se obtiene el id guardado en la sesion
    is_admin = False # Valor por defecto: no es admin por defecto para seguridad

    try: # Buscamos al usuario en MongoDB para obtener su rol
        current_user = usuarios.objects.get(id=user_id)
        if current_user.rol == True:
            is_admin = True # Si tiene rol=True, lo marcamos como admin
    except usuarios.DoesNotExist: # Si el usuario no existe, lo deslogueamos y mandamos al login inmedidatamente
        try:
            del request.session['user_id'] #los del son para limpiar la sesion
            del request.session['user_nombre']
        except KeyError: pass
        return redirect('login') #y aca redirigimos al login

    # Pasamos el nombre Y si es admin (True/False) a la plantilla
    context = {
        'user_nombre': request.session.get('user_nombre'),
        'is_admin': is_admin 
    }
    return render(request, 'prueba/home.html', context) #Muestra la plantilla home.html






def logout_view(request): #Funcion/vista para cerrar la sesion xd
    try:
        del request.session['user_id'] #los del son para limpiar la sesion
        del request.session['user_nombre']
    except KeyError:
        pass

    return redirect('login') #Siempre redirige al login





#EN ESTADO BETA NO TOCAAAR
def ingresar_view(request):
    if 'user_id' not in request.session:
        return redirect('login')
    
    if request.method == 'POST':
        form = CalificacionModalForm(request.POST)
        if form.is_valid():
            nueva_calificacion = Calificacion(**form.cleaned_data)
            nueva_calificacion.save()
            return redirect('home')
    else:
        #Leemos todos los datos que vienen del modal por la URL
        initial_data = {
            'Mercado': request.GET.get('mercado', None),
            'Ejercicio': request.GET.get('ejercicio', None),
            'Instrumento': request.GET.get('instrumento', None),
            'FechaPago': request.GET.get('fecha_pago', None),
            'SecuenciaEvento': request.GET.get('secuencia', None),
        }
        
        #Creamos el formulario con esos valores iniciales
        form = CalificacionModalForm(initial=initial_data)

    return render(request, 'prueba/ingresar.html', {'form': form})






#Funcion/vista para el modulo de administrar
def administrar_view(request):
    if 'user_id' not in request.session: #Verificar si está logueado
        return redirect('login')
    user_id = request.session['user_id']
    try: #Verifica si es admin
        current_user = usuarios.objects.get(id=user_id)
        if current_user.rol == True:
            todos_los_usuarios = usuarios.objects.all() #Obtiene la lista completa de usuarios
            context = { # Se inicia la plantilla a la espera de datos
                'user_nombre': request.session.get('user_nombre'),
                'lista_usuarios': todos_los_usuarios # Pasamos la lista a la plantilla
            }
            return render(request, 'prueba/administrar.html', context) #Muestra la plantilla administrar.html
        else:
            # Si NO es admin, acceso denegado
            return HttpResponseForbidden("<h1>Acceso Denegado</h1><p>No tienes permisos de administrador para ver esta página.</p><a href='/home/'>Volver al inicio</a>")

    except usuarios.DoesNotExist: #Si el usuario de la sesión no existe, limpiamos y al login
        try:
            del request.session['user_id']
            del request.session['user_nombre']
        except KeyError: pass
        return redirect('login')






#Funcion/vista para el modulo de crear usuario
@require_POST #Solo permite peticiones POST
def crear_usuario_view(request):
    #Verificar si el que hace la petición es admin
    if 'user_id' not in request.session: return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)
    try: #chequeo de rol
        admin_user = usuarios.objects.get(id=request.session['user_id'])
        if not admin_user.rol: return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    except usuarios.DoesNotExist: return JsonResponse({'success': False, 'error': 'Admin no válido'}, status=401)

    form = UsuarioForm(request.POST) #Validar los datos recibidos en el POST usando el formulario
    if form.is_valid(): #¿Pasó la validación (requeridos, email, correo no repetido)?
        try:
            nuevo_usuario = usuarios( #Crea un objeto usuarios con los datos limpios del form
                nombre=form.cleaned_data['nombre'],
                correo=form.cleaned_data['correo'],
                contrasena=form.cleaned_data['contrasena'],
                rol=form.cleaned_data['rol']
            )
            nuevo_usuario.save() #Guarda en MongoDB
            return JsonResponse({'success': True}) #Responde al JS con éxito
        except Exception as e:#Si ocurre un error al guardar en BD
            print(f"Error al crear usuario: {e}") # Log para el servidor
            # --- ¡RESPUESTA CORRECTA EN ERROR! ---
            return JsonResponse({'success': False, 'error': f'Error interno al guardar: {e}'}, status=500) 
    else:
        print("Errores de formulario (Crear):", form.errors.as_json()) # Log para el servidor
        return JsonResponse({'success': False, 'error': form.errors.as_json()}, status=400) 






#Funcion/vista para el modulo de eliminar usuario
@require_POST #Solo permite peticiones POST
def eliminar_usuarios_view(request):
    #Verificar si el que hace la petición es admin
    if 'user_id' not in request.session: return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)
    try: #chequeo de rol
        admin_user = usuarios.objects.get(id=request.session['user_id'])
        if not admin_user.rol: return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    except usuarios.DoesNotExist: return JsonResponse({'success': False, 'error': 'Admin no válido'}, status=401)
    try: #Leer la lista de IDs del cuerpo JSON de la petición
        data = json.loads(request.body) #Parsea el JSON enviado por fetch
        user_ids_to_delete = data.get('user_ids', []) #Extrae la lista de ID
        if not isinstance(user_ids_to_delete, list) or not user_ids_to_delete: #Verifica que sea una lista y no esté vacía
             return JsonResponse({'success': False, 'error': 'Lista de IDs inválida'}, status=400)
    except json.JSONDecodeError: # Si el cuerpo no era JSON válido
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

    try: #Proceso de Intentar eliminar los usuarios
        if request.session['user_id'] in user_ids_to_delete: #verificar no autoeliminarse
             return JsonResponse({'success': False, 'error': 'No puedes eliminarte a ti mismo'}, status=400)
        delete_result = usuarios.objects(id__in=user_ids_to_delete).delete() 
        print(f"Usuarios eliminados: {delete_result}") # Log para el servidor
        return JsonResponse({'success': True, 'deleted_count': delete_result}) 
    except Exception as e:
        print(f"Error al eliminar usuarios: {e}") # Log para el servidor
        # --- ¡RESPUESTA CORRECTA EN ERROR! ---
        return JsonResponse({'success': False, 'error': f'Error interno al eliminar: {e}'}, status=500) 







#Vista para obtener a los usuarios para el modificar (evaluandose su uso)
@require_GET
def obtener_usuario_view(request, user_id):
     #verificación admin
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




#Funcion/vista para el modulo de modificar usuario
@require_POST #Solo permite peticiones POST
def modificar_usuario_view(request):
    if 'user_id' not in request.session: #Verificar si el que hace la petición es admin
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)
    try: #chequeo de rol
        admin_user = usuarios.objects.get(id=request.session['user_id'])
        if not admin_user.rol:
            return JsonResponse({'success': False, 'error': 'No autorizado'}, status=403)
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Admin no válido'}, status=401)

    #Validacion de datos
    user_id = request.POST.get('user_id') or request.POST.get('id')  # aceptación por si hay nombre distinto
    if not user_id: # Si no se recibe el ID del usuario a modificar, devuelve error 400
        return JsonResponse({'success': False, 'error': 'Falta user_id en la petición'}, status=400)

    nombre = request.POST.get('nombre', '').strip() # Obtiene 'nombre' y 'correo' del POST
    correo = request.POST.get('correo', '').strip()
    contrasena = request.POST.get('contrasena', '')  #Obtiene la contrasena (puede estar vacía si no se quiere cambiar)
    rol_raw = request.POST.get('rol', 'false') # Obtiene el valor  del checkbox rol puede ser on. Por defecto es false
    rol = str(rol_raw).lower() in ('true', '1', 'on', 'yes')

    if not nombre or not correo: #Verifica que nombre y correo no estén vacíos
        return JsonResponse({'success': False, 'error': 'Nombre y correo son obligatorios.'}, status=400)

    try: #Buscar y Actualizar el Usuario en MongoDB
        usuario = usuarios.objects.get(id=user_id) #Busca al usuario que se quiere modificar usando el user_id recibido
        usuario.nombre = nombre # Actualiza los campos de usuario con los nuevos valores
        usuario.correo = correo #Esto no valida si el correo ya existe en otro usuario
        # Solo actualizar contraseña si se entregó una
        if contrasena:
            usuario.contrasena = contrasena

        usuario.rol = rol #Actualiza el rol con el valor booleano
        usuario.save() #Guarda todos los cambios hechos al objeto usuario en la base de datos MongoDB
        return JsonResponse({'success': True})
    except usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        # LOG para servidor
        print("Error interno modificar_usuario_view:", e)
        return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'}, status=500)