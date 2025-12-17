# Crear Base de Datos y Usuario Administrador

Este documento explica cómo crear la base de datos "NUPPY" en MongoDB Compass y cómo crear un usuario administrador directamente en la base de datos usando el shell de Django.

## Requisitos Previos

- Tener el proyecto Django configurado y funcionando
- Tener acceso a la terminal/consola
- Tener MongoDB instalado y corriendo
- Tener MongoDB Compass instalado

## Parte 1: Crear la Base de Datos "NUPPY" en MongoDB Compass

### 1. Abrir MongoDB Compass

Abre la aplicación MongoDB Compass en tu computadora.

### 2. Conectar a MongoDB

- Si MongoDB está corriendo localmente, usa la cadena de conexión: `mongodb://localhost:27017`
- Si tienes una conexión remota, usa la cadena de conexión correspondiente
- Haz clic en "Connect" para conectarte

### 3. Crear la Base de Datos "NUPPY"

Una vez conectado, sigue estos pasos:

1. En el panel izquierdo, verás una lista de bases de datos existentes
2. Haz clic en el botón **"+"** o en **"Create Database"** (Crear Base de Datos)
3. Se abrirá un diálogo para crear una nueva base de datos
4. Ingresa los siguientes valores:
   - **Database Name:** `nuppy`
   - **Collection Name:** `usuarios`
5. Haz clic en **"Create Database"**

### 4. Verificar la Creación

- Deberías ver la base de datos `NUPPY` en el panel izquierdo
- Al hacer clic en ella, verás las colecciones (inicialmente puede estar vacía)

### Nota sobre Colecciones

Las colecciones se crearán automáticamente cuando Django guarde el primer documento en cada modelo. Por ejemplo:
- `usuarios` - se creará cuando guardes el primer usuario
- `calificaciones` - se creará cuando guardes la primera calificación

### Configuración en Django

Asegúrate de que tu archivo `settings.py` tenga configurada la conexión a MongoDB con el nombre de base de datos correcto:

```python
MONGODB_DATABASES = {
    'default': {
        'name': 'nuppy',
        'host': 'localhost',
        'port': 27017,
    }
}
```

## Parte 2: Crear Usuario Administrador

### 1. Iniciar el Shell de Django

Abre tu terminal/consola y navega hasta la carpeta raíz del proyecto Django (donde está el archivo `manage.py`), luego ejecuta:

```bash
python manage.py shell
```

### 2. Importar el Modelo y la Función de Hashing

Una vez dentro del shell, importa el modelo de usuarios y la función para hashear contraseñas:

```python
from prueba.models import usuarios
from prueba.views import _hash_password
```

### 3. Definir la Contraseña Plana y Hashearla

Define la contraseña que quieres usar para el administrador y luego hasheala:

```python
contrasena_plana = "MiContrasenaDeAdmin"
contrasena_hasheada = _hash_password(contrasena_plana)
```

**Nota:** Reemplaza `"MiContrasenaDeAdmin"` con la contraseña que desees usar. Asegúrate de que cumpla con los requisitos de seguridad (mínimo 8 caracteres, mayúsculas, minúsculas y símbolos especiales).

### 4. Crear la Instancia del Usuario

Crea una nueva instancia del modelo `usuarios` con los datos del administrador:

```python
admin = usuarios(
    nombre="Admin Maestro",
    correo="admin@sistema.com", 
    contrasena=contrasena_hasheada, 
    rol=True
)
```

**Nota:** 
- Reemplaza `"Admin Maestro"` con el nombre que desees para el administrador
- Reemplaza `"admin@sistema.com"` con el correo electrónico que desees usar
- `rol=True` establece que el usuario será administrador

### 5. Guardar en MongoDB

Guarda el usuario en la base de datos:

```python
admin.save()
```

### 6. Verificar el ID (Opcional)

Para confirmar que el usuario se creó correctamente, puedes imprimir su ID:

```python
print(admin.id)
```

### 7. Salir del Shell

Una vez completado, sal del shell de Django:

```python
exit()
```

## Ejemplo Completo

Aquí tienes un ejemplo completo de todo el proceso en una sola secuencia:

```python
# Iniciar shell: python manage.py shell

from prueba.models import usuarios
from prueba.views import _hash_password

contrasena_plana = "Admin123!@#"
contrasena_hasheada = _hash_password(contrasena_plana)

admin = usuarios(
    nombre="Administrador Principal",
    correo="admin@nuppy.com", 
    contrasena=contrasena_hasheada, 
    rol=True
)

admin.save()

print(f"Usuario admin creado con ID: {admin.id}")
print(f"Correo: {admin.correo}")
print(f"Rol admin: {admin.rol}")

exit()
```

## Verificación

Después de crear el usuario, puedes verificar que se creó correctamente iniciando sesión en la aplicación web con el correo y contraseña que definiste.

## Notas Importantes

-  **Seguridad**: Asegúrate de usar una contraseña segura para el administrador
- **Correo único**: El correo electrónico debe ser único en la base de datos. Si intentas crear un usuario con un correo que ya existe, obtendrás un error
- **Rol**: Solo los usuarios con `rol=True` tienen permisos de administrador
-  **Contraseña**: La contraseña se hashea antes de guardarse, por lo que no se almacena en texto plano

## Solución de Problemas

### Error: "Este correo electrónico ya está registrado"
- El correo que intentas usar ya existe en la base de datos
- Usa un correo diferente o elimina el usuario existente primero

### Error: "Module not found" o "Import error"
- Asegúrate de estar en el directorio correcto del proyecto
- Verifica que el entorno virtual esté activado (si usas uno)
- Verifica que todas las dependencias estén instaladas

### Error al guardar
- Verifica que MongoDB esté corriendo
- Verifica la conexión a la base de datos en `settings.py`
- Revisa los logs de Django para más detalles del error

