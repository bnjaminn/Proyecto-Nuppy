from django.shortcuts import render, redirect
from .formulario import LoginForm
from .models import usuarios  # importamos la clase usuarios de models para trabajar onda aca rescatamos los datos del documento los cuales usaremos para trabajar

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


def home_view(request): #paGINA del home que se cambiara por el dashboard esperado 
    if 'user_id' not in request.session:
        return redirect('login')

    context = {
        'user_nombre': request.session.get('user_nombre')
    }
    return render(request, 'prueba/home.html', context)


def logout_view(request): #pagina para cerrar la sesion xd
    try:
        del request.session['user_id']
        del request.session['user_nombre']
    except KeyError:
        pass

    return redirect('login')