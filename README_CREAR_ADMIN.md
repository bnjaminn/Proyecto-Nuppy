# Crear Usuario Administrador en la Base de Datos

Este documento explica cómo crear un usuario administrador directamente en la base de datos usando el shell de Django.

## Requisitos Previos

- Tener el proyecto Django configurado y funcionando
- Tener acceso a la terminal/consola
- Tener MongoDB corriendo y configurado

## Pasos para Crear un Usuario Admin

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

