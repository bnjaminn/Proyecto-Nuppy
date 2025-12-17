/**
 * ADMINISTRAR.JS - JavaScript para Administración de Usuarios
 * ============================================
 * 
 * POR QUÉ ESTE SCRIPT ES IMPORTANTE:
 * - Proporciona toda la funcionalidad de administración de usuarios en el cliente
 * - Permite crear, modificar y eliminar usuarios sin recargar la página
 * - Valida formularios en el cliente antes de enviarlos al servidor
 * - Muestra notificaciones y mensajes de carga para mejor UX
 * - Previene auto-eliminación y otros errores comunes
 * 
 * CÓMO FUNCIONA:
 * 1. Al cargar la página, inicializa todos los event listeners
 * 2. Permite seleccionar usuarios haciendo clic en sus tarjetas
 * 3. Muestra modales para crear y modificar usuarios
 * 4. Valida contraseñas en tiempo real con indicadores visuales
 * 5. Envía peticiones AJAX al servidor para operaciones CRUD
 * 6. Muestra notificaciones de éxito/error al usuario
 * 
 * FUNCIONALIDADES PRINCIPALES:
 * - Selección/deselección de usuarios (múltiple selección)
 * - Crear nuevos usuarios (con validación de contraseña)
 * - Modificar usuarios existentes (con validación opcional de contraseña)
 * - Eliminar usuarios (con confirmación y prevención de auto-eliminación)
 * - Validación de formularios en el cliente
 * - Sistema de notificaciones elegantes
 * - Indicadores de carga durante operaciones asíncronas
 * ============================================
 */

// ============================================
// SISTEMA DE NOTIFICACIONES
// ============================================
// Muestra notificaciones elegantes en la esquina superior de la pantalla.
// Las notificaciones aparecen y desaparecen automáticamente después de 4 segundos.
// 
// Tipos de notificación:
//   - success: Éxito (verde, icono ✓)
//   - error: Error (rojo, icono ✕)
//   - warning: Advertencia (amarillo, icono ⚠)
//   - info: Información (azul, icono ℹ)

// ============================================
// FUNCIÓN: mostrarNotificacion(mensaje, tipo)
// ============================================
// Propósito: Crea y muestra una notificación temporal en la esquina de la pantalla.
// 
// Parámetros:
//   - mensaje (string): Texto a mostrar en la notificación
//   - tipo (string, opcional): Tipo de notificación ('success', 'error', 'warning', 'info')
//     Por defecto: 'success'
// 
// Retorna: void
// 
// Flujo de ejecución:
//   1. Crea el contenedor de notificaciones si no existe
//   2. Crea un elemento div para la notificación
//   3. Añade el icono correspondiente según el tipo
//   4. Agrega la notificación al contenedor
//   5. Anima la entrada de la notificación
//   6. Programa la eliminación automática después de 4 segundos
// 
// Ejemplo de uso:
//   mostrarNotificacion('Usuario creado exitosamente', 'success');
//   mostrarNotificacion('Error al guardar', 'error');
// ============================================
function mostrarNotificacion(mensaje, tipo = 'success') {
    // ========== CREAR CONTENEDOR SI NO EXISTE ==========
    // El contenedor de notificaciones es un div único que contiene todas las notificaciones
    let notificacionesContainer = document.getElementById('notificaciones-container');
    if (!notificacionesContainer) {
        // Si no existe, crearlo y agregarlo al body
        notificacionesContainer = document.createElement('div');
        notificacionesContainer.id = 'notificaciones-container';
        document.body.appendChild(notificacionesContainer);
    }

    // ========== CREAR ELEMENTO DE NOTIFICACIÓN ==========
    // Crear un nuevo div para esta notificación específica
    const notificacion = document.createElement('div');
    
    // Asignar clases CSS según el tipo de notificación
    // Las clases CSS proporcionan los estilos visuales (color, borde, etc.)
    notificacion.className = `notificacion notificacion-${tipo}`;
    
    // Establecer el texto del mensaje
    notificacion.textContent = mensaje;
    
    // ========== AÑADIR ICONO SEGÚN EL TIPO ==========
    // Cada tipo de notificación tiene un icono diferente para mejor identificación visual
    const icono = document.createElement('span');
    icono.className = 'notificacion-icono';
    
    // Asignar el icono correspondiente según el tipo usando Bootstrap Icons
    if (tipo === 'success') {
        icono.innerHTML = '<i class="bi bi-check-circle-fill"></i>'; // Check verde para éxito
    } else if (tipo === 'error') {
        icono.innerHTML = '<i class="bi bi-x-circle-fill"></i>'; // X roja para error
    } else if (tipo === 'warning') {
        icono.innerHTML = '<i class="bi bi-exclamation-triangle-fill"></i>'; // Alerta amarilla para advertencia
    } else {
        icono.innerHTML = '<i class="bi bi-info-circle-fill"></i>'; // Información azul para info
    }
    
    // Insertar el icono al inicio de la notificación (antes del texto)
    notificacion.insertBefore(icono, notificacion.firstChild);

    // ========== AGREGAR NOTIFICACIÓN AL CONTENEDOR ==========
    // Agregar la notificación al contenedor para que sea visible
    notificacionesContainer.appendChild(notificacion);

    // ========== ANIMAR ENTRADA ==========
    // Agregar la clase 'show' después de un pequeño delay para activar la animación CSS
    // El delay de 10ms asegura que el elemento esté en el DOM antes de animar
    setTimeout(() => notificacion.classList.add('show'), 10);

    // ========== ELIMINACIÓN AUTOMÁTICA ==========
    // Programar la eliminación automática de la notificación después de 4 segundos
    // Primero remueve la clase 'show' para animar la salida (300ms de animación CSS)
    // Luego elimina el elemento del DOM completamente
    setTimeout(() => {
        // Remover clase 'show' para activar animación de salida
        notificacion.classList.remove('show');
        // Esperar a que termine la animación (300ms) y luego eliminar el elemento
        setTimeout(() => notificacion.remove(), 300);
    }, 4000);
}

// ============================================
// SISTEMA DE INDICADORES DE CARGA
// ============================================
// Muestra un overlay con spinner de carga para indicar al usuario que una operación está en progreso.
// Útil durante peticiones AJAX, creación/modificación de usuarios, etc.

// ============================================
// FUNCIÓN: mostrarCarga(mensaje)
// ============================================
// Propósito: Muestra un overlay de carga con un spinner y mensaje personalizado.
// 
// Parámetros:
//   - mensaje (string, opcional): Mensaje a mostrar junto al spinner
//     Por defecto: 'Procesando...'
// 
// Retorna: void
// 
// Flujo de ejecución:
//   1. Verifica si el overlay de carga ya existe
//   2. Si no existe, lo crea con el HTML del spinner y mensaje
//   3. Si existe, solo actualiza el mensaje
//   4. Muestra el overlay cambiando su display a 'flex'
// 
// Ejemplo de uso:
//   mostrarCarga('Creando usuario...');
//   mostrarCarga('Eliminando usuario...');
// ============================================
function mostrarCarga(mensaje = 'Procesando...') {
    // Buscar el overlay de carga si ya existe usando su ID 'carga-overlay'
    // getElementById busca un elemento en el documento con el ID especificado
    // Si no existe, devuelve null
    // Usar 'let' en lugar de 'const' porque puede necesitar reasignarse si no existe
    let overlayCarga = document.getElementById('carga-overlay');
    
    // Verificar si el overlay de carga no existe (es null o undefined)
    // Si no existe, necesitamos crearlo
    if (!overlayCarga) {
        // ========== CREAR EL OVERLAY DE CARGA ==========
        // Crear un nuevo elemento div para el overlay de carga
        // createElement crea un nuevo elemento HTML del tipo especificado
        // Este elemento aún no está en el DOM, solo existe en memoria
        overlayCarga = document.createElement('div');
        // Asignar el ID 'carga-overlay' al nuevo elemento
        // El ID permite identificarlo fácilmente después
        // También permite aplicar estilos CSS específicos a este elemento
        overlayCarga.id = 'carga-overlay';
        
        // Asignar el HTML interno del overlay
        // innerHTML permite establecer el contenido HTML del elemento
        // Usar template literals (backticks) para incluir el parámetro 'mensaje'
        // Estructura HTML del overlay:
        // - Un div contenedor con clase 'carga-spinner' que contiene todo
        // - Un div con clase 'spinner' que muestra la animación CSS de rotación
        // - Un párrafo con clase 'carga-mensaje' que muestra el mensaje personalizado
        // El mensaje se interpola usando ${mensaje} dentro del template literal
        overlayCarga.innerHTML = `
            <div class="carga-spinner">
                <div class="spinner"></div>
                <p class="carga-mensaje">${mensaje}</p>
            </div>
        `;
        
        // Agregar el overlay al final del body del documento
        // appendChild agrega un elemento hijo al final de la lista de hijos del elemento padre
        // document.body es una referencia al elemento <body> del documento
        // Esto hace que el overlay sea visible en la página
        document.body.appendChild(overlayCarga);
    } else {
        // ========== ACTUALIZAR EL MENSAJE SI EL OVERLAY YA EXISTE ==========
        // Si el overlay ya existe, no necesitamos recrearlo
        // Solo necesitamos actualizar el mensaje para evitar crear múltiples overlays
        
        // Buscar el elemento del mensaje dentro del overlay usando querySelector
        // querySelector busca el primer elemento que coincida con el selector CSS '.carga-mensaje'
        // '.carga-mensaje' es un selector de clase que busca elementos con esa clase
        const mensajeElement = overlayCarga.querySelector('.carga-mensaje');
        // Verificar si el elemento del mensaje existe antes de intentar modificarlo
        // Esto previene errores si la estructura HTML cambió
        if (mensajeElement) {
            // Actualizar el contenido de texto del mensaje con el nuevo valor
            // textContent establece el texto plano del elemento (sin HTML)
            // Usar textContent en lugar de innerHTML para evitar inyección de HTML
            mensajeElement.textContent = mensaje;
        }
    }
    
    // Mostrar el overlay cambiando su propiedad display a 'flex'
    // 'flex' activa el modelo de caja flexbox que permite centrar el contenido fácilmente
    // El overlay cubre toda la pantalla y previene interacciones del usuario con otros elementos
    // Esto indica visualmente que una operación está en progreso
    overlayCarga.style.display = 'flex';
}

// ============================================
// FUNCIÓN: ocultarCarga()
// ============================================
// Propósito: Oculta el overlay de carga.
// 
// Retorna: void
// 
// Flujo de ejecución:
//   1. Obtiene el overlay de carga
//   2. Si existe, cambia su display a 'none' para ocultarlo
// 
// Ejemplo de uso:
//   ocultarCarga();
// 
// Nota: Se debe llamar después de completar una operación asíncrona para
//       permitir que el usuario vuelva a interactuar con la página.
// ============================================
function ocultarCarga() {
    // Buscar el overlay de carga usando su ID 'carga-overlay'
    // getElementById busca un elemento en el documento con el ID especificado
    // Devuelve el elemento si existe, o null si no existe
    const overlayCarga = document.getElementById('carga-overlay');
    // Verificar si el overlay existe antes de intentar modificarlo
    // Esto previene errores de JavaScript si el elemento no está en el DOM
    if (overlayCarga) {
        // Ocultar el overlay cambiando su propiedad display a 'none'
        // 'none' hace que el elemento no sea visible y no ocupe espacio en el DOM
        // Esto efectivamente oculta el indicador de carga y permite que el usuario vuelva a interactuar
        // con la página después de que la operación asíncrona haya terminado
        overlayCarga.style.display = 'none';
    }
}

// ============================================
// FUNCIÓN: limpiarMensajeError(msg)
// ============================================
// Propósito: Convierte mensajes de error técnicos del servidor en mensajes amigables para el usuario.
// 
// Parámetros:
//   - msg (string): Mensaje de error original del servidor o excepción
// 
// Retorna:
//   - string: Mensaje de error limpio y amigable para mostrar al usuario
// 
// Flujo de ejecución:
//   1. Valida que el mensaje exista, si no, retorna "Error desconocido"
//   2. Convierte el mensaje a minúsculas para comparación sin case-sensitive
//   3. Busca patrones específicos en el mensaje para identificar el tipo de error
//   4. Retorna un mensaje amigable correspondiente al tipo de error encontrado
//   5. Si no encuentra un patrón específico, limpia el mensaje (remueve HTML) y lo trunca
// 
// Tipos de errores manejados:
//   - Duplicate key / Correo / Email: Correo ya registrado
//   - 400 / Bad request: Error de validación
//   - 500: Error interno del servidor
//   - CSRF / Token: Error de seguridad
//   - JSON / Syntax: Error al procesar respuesta
//   - Otros: Mensaje original limpiado y truncado
// 
// Ejemplo de uso:
//   const errorLimpio = limpiarMensajeError(error.message);
//   mostrarMensaje('Error', errorLimpio, 'error');
// ============================================
function limpiarMensajeError(msg) {
    // ========== VALIDAR QUE EL MENSAJE EXISTA ==========
    // Verificar si el mensaje es null, undefined, vacío o cualquier valor falsy
    // Si el mensaje no existe, retornar un mensaje de error genérico
    // Esto previene errores al intentar procesar un mensaje nulo
    if (!msg) {
        // Retornar un mensaje de error genérico si no hay mensaje
        // Este es el mensaje que se mostrará al usuario si no hay información específica
        return "Error desconocido.";
    }
    
    // ========== CONVERTIR MENSAJE A MINÚSCULAS ==========
    // Convertir el mensaje a minúsculas usando el método toLowerCase()
    // Esto permite comparaciones sin case-sensitive (ignorar mayúsculas/minúsculas)
    // Por ejemplo, "ERROR", "Error" y "error" serán tratados igual
    // Guardar el resultado en una constante 'lower' para usarlo en las comparaciones
    const lower = msg.toLowerCase();
    
    // ========== DETECTAR TIPOS DE ERRORES ESPECÍFICOS ==========
    // Buscar patrones específicos en el mensaje de error para identificar el tipo
    // Cada tipo de error tiene un mensaje amigable diferente para el usuario
    
    // Error: Correo duplicado (base de datos)
    // Verificar solo patrones MUY específicos de error de correo duplicado
    // NO buscar solo "correo" ya que puede aparecer en otros contextos (como en mensajes de éxito)
    // Solo detectar si el mensaje contiene explícitamente el mensaje de error de correo duplicado
    const esErrorCorreoDuplicado = 
        lower.includes("duplicate key") || 
        lower.includes("este correo electrónico ya está registrado") ||
        (lower.includes("correo") && lower.includes("ya está registrado") && !lower.includes("éxito") && !lower.includes("exitosamente") && !lower.includes("creado"));
    
    if (esErrorCorreoDuplicado) {
        // Retornar un mensaje amigable sobre correo duplicado
        // Este mensaje es más claro que el mensaje técnico original
        return "Este correo electrónico ya está registrado.";
    }
    // Error 400: Solicitud incorrecta (validación fallida)
    // Verificar si el mensaje contiene "400" o "bad request"
    // El código 400 indica que la solicitud del cliente fue incorrecta
    // Generalmente significa que los datos enviados no pasaron la validación del servidor
    else if (lower.includes("400") || lower.includes("bad request")) {
        // Retornar un mensaje que indica que debe verificar los datos ingresados
        return "Verifica los datos ingresados. Es posible que el correo ya exista.";
    }
    // Error 500: Error interno del servidor
    // Verificar si el mensaje contiene "500"
    // El código 500 indica un error en el servidor, no es culpa del usuario
    else if (lower.includes("500")) {
        // Retornar un mensaje que indica que es un problema del servidor
        // No culpamos al usuario, simplemente le pedimos que intente más tarde
        return "Error interno del servidor. Intenta más tarde.";
    }
    // Error CSRF: Token de seguridad inválido
    // Verificar si el mensaje contiene "csrf" o "token"
    // CSRF (Cross-Site Request Forgery) es un error de seguridad
    // Requiere recargar la página para obtener un nuevo token
    else if (lower.includes("csrf") || lower.includes("token")) {
        // Retornar un mensaje que indica que debe recargar la página
        return "Error de seguridad. Recarga la página e inténtalo nuevamente.";
    }
    // Error de JSON: Respuesta malformada del servidor
    // Verificar si el mensaje contiene "json" o "syntax"
    // Esto indica un problema al parsear la respuesta JSON del servidor
    else if (lower.includes("json") || lower.includes("syntax")) {
        // Retornar un mensaje sobre error al procesar la respuesta
        return "Error al procesar la respuesta del servidor.";
    }
    
    // ========== LIMPIAR Y TRUNCAR MENSAJE GENÉRICO ==========
    // Si no se detecta un tipo específico de error, limpiar el mensaje original
    // Esto asegura que el mensaje sea seguro y legible
    
    // Paso 1: Remover cualquier HTML del mensaje usando regex
    // replace() reemplaza todas las coincidencias del patrón con una cadena vacía
    // Patrón regex: /<[^>]*>?/gm
    //   - <[^>]*>: Coincide con cualquier etiqueta HTML (<tag> o </tag>)
    //   - ?: Hace el match opcional (para casos como < > sin etiqueta)
    //   - g: flag global (busca todas las coincidencias, no solo la primera)
    //   - m: flag multilínea (permite coincidencias en múltiples líneas)
    // Esto previene inyección de HTML en el mensaje de error
    
    // Paso 2: Truncar el mensaje a 300 caracteres usando slice()
    // slice(0, 300) toma los primeros 300 caracteres del string
    // Si el mensaje es más largo, se corta; si es más corto, se mantiene igual
    // Esto asegura que el mensaje no sea demasiado largo para mostrar al usuario
    
    // Retornar el mensaje limpio y truncado
    return msg.replace(/<[^>]*>?/gm, "").slice(0, 300);
}

// INICIALIZACIÓN AL CARGAR EL DOCUMENTO
// ======================================
// Espera a que TODO el HTML esté cargado y listo antes de ejecutar el código.
// Esto asegura que todos los elementos del DOM estén disponibles.
document.addEventListener('DOMContentLoaded', function() { 
    console.log("DOM Cargado. Iniciando TODOS los scripts...");
    
    // Inicializar el modal de mensajes si las funciones están disponibles
    // (el modal se define en home.js y está disponible globalmente)
    if (typeof inicializarModalMensaje === 'function') {
        inicializarModalMensaje();
    } 

    // ============================================
    // SECCIÓN 1: SELECCIÓN/DESELECCIÓN DE USUARIOS
    // ============================================
    // Permite seleccionar usuarios haciendo clic en sus tarjetas.
    // Los botones de modificar/eliminar se habilitan según la cantidad seleccionada.
    const userCards = document.querySelectorAll('.user-card');
    const btnModificar = document.querySelector('#btn-modificar-usuario');
    const btnEliminar = document.querySelector('#btn-eliminar-usuario');  
    let selectedUserIds = [];

    function actualizarBotonesAccion() {
        const selectedCards = document.querySelectorAll('.user-card.selected');
        const count = selectedCards.length;
        
        if (btnModificar) btnModificar.disabled = (count !== 1);
        if (btnEliminar) btnEliminar.disabled = (count === 0); 

        selectedUserIds = Array.from(selectedCards).map(card => card.dataset.userId);
        console.log(count + " usuario(s) seleccionado(s):", selectedUserIds);
    }

    userCards.forEach(card => {
        card.addEventListener('click', () => {
            card.classList.toggle('selected');
            actualizarBotonesAccion();
        });
    });

    actualizarBotonesAccion();
    console.log("Lógica de selección de usuarios inicializada.");

    //SECCION 2: Modal Crear Usuario
    const modalCrearOverlay = document.getElementById('crear-usuario-modal-overlay');
    const btnAbrirCrear = document.getElementById('btn-abrir-crear-usuario'); 
    const btnCerrarCrear = document.getElementById('btn-cerrar-crear-usuario');
    const btnCerrarCrearX = document.getElementById('btn-cerrar-crear-usuario-x');
    const formCrearUsuario = document.getElementById('form-crear-usuario');

    // Función auxiliar para actualizar el estado visual de un requisito
    function actualizarRequisito(id, cumplido) {
        const requisito = document.getElementById(id);
        if (!requisito) return;
        
        const icon = requisito.querySelector('.requisito-icon');
        const texto = requisito.querySelector('.requisito-texto');
        
        if (icon && texto) {
            if (cumplido) {
                icon.innerHTML = '<i class="bi bi-check-circle-fill"></i>';
                icon.style.color = '#28a745';
                texto.style.color = '#28a745';
                requisito.style.opacity = '1';
            } else {
                icon.innerHTML = '<i class="bi bi-x-circle"></i>';
                icon.style.color = '#dc3545';
                texto.style.color = '#666';
                requisito.style.opacity = '0.6';
            }
        }
    }
    
    // Función para resetear todos los requisitos a estado inicial
    function resetearRequisitos() {
        const requisitos = ['req-longitud', 'req-mayuscula', 'req-minuscula', 'req-simbolo'];
        requisitos.forEach(id => {
            actualizarRequisito(id, false);
        });
    }

    function abrirModalCrear() {
        if (!modalCrearOverlay) return;
        if (formCrearUsuario) formCrearUsuario.reset();
        // Resetear indicadores de requisitos
        resetearRequisitos();
        modalCrearOverlay.style.display = 'flex';
    }

    function cerrarModalCrear() {
        if (!modalCrearOverlay) return;
        modalCrearOverlay.style.display = 'none';
    }

    if (btnAbrirCrear) btnAbrirCrear.addEventListener('click', abrirModalCrear);
    if (btnCerrarCrear) btnCerrarCrear.addEventListener('click', cerrarModalCrear);
    if (btnCerrarCrearX) btnCerrarCrearX.addEventListener('click', cerrarModalCrear);
    // Event listener para cerrar modal al hacer clic fuera eliminado por solicitud del usuario
    
    // ========== VALIDACIÓN EN TIEMPO REAL DE CONTRASEÑA ==========
    const inputContrasena = document.getElementById('crear-contrasena');
    if (inputContrasena) {
        inputContrasena.addEventListener('input', function() {
            const contrasena = this.value;
            
            // Verificar cada requisito
            const tieneLongitud = contrasena.length >= 8;
            const tieneMayuscula = /[A-Z]/.test(contrasena);
            const tieneMinuscula = /[a-z]/.test(contrasena);
            const tieneSimbolo = /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(contrasena);
            
            // Actualizar indicadores visuales
            actualizarRequisito('req-longitud', tieneLongitud);
            actualizarRequisito('req-mayuscula', tieneMayuscula);
            actualizarRequisito('req-minuscula', tieneMinuscula);
            actualizarRequisito('req-simbolo', tieneSimbolo);
        });
    }
    
    if (formCrearUsuario) {
        formCrearUsuario.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // Validación del lado del cliente para contraseñas
            const contrasena = document.getElementById('crear-contrasena').value;
            const confirmarContrasena = document.getElementById('crear-confirmar-contrasena').value;
            
            // Verificar que las contraseñas coincidan
            if (contrasena !== confirmarContrasena) {
                mostrarMensaje('Error', 'Las contraseñas no coinciden. Por favor, verifique que ambas sean iguales.', 'error');
                return;
            }
            
            // Verificar requisitos de la contraseña
            const errores = [];
            if (contrasena.length < 8) {
                errores.push('La contraseña debe tener al menos 8 caracteres.');
            }
            if (!/[A-Z]/.test(contrasena)) {
                errores.push('La contraseña debe contener al menos una letra mayúscula.');
            }
            if (!/[a-z]/.test(contrasena)) {
                errores.push('La contraseña debe contener al menos una letra minúscula.');
            }
            if (!/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(contrasena)) {
                errores.push('La contraseña debe contener al menos un símbolo especial (!@#$%^&*()_+-=[]{}|;:,.<>?).');
            }
            
            if (errores.length > 0) {
                mostrarMensaje('Error de validación', errores.join('\n'), 'error');
                return;
            }
            
            mostrarCarga('Creando usuario...');

            const formData = new FormData(formCrearUsuario);
            const url = formCrearUsuario.action;
            if (!formData.has('rol')) { 
                formData.append('rol', 'false'); 
            } else { 
                formData.set('rol', 'true'); 
            }

            fetch(url, { 
                method: 'POST', 
                body: formData,
                headers: { 'X-CSRFToken': formData.get('csrfmiddlewaretoken') }
            })
            .then(response => {
                // Siempre intentar parsear como JSON primero
                return response.json().then(data => {
                    // Si la respuesta no es OK, lanzar error
                    if (!response.ok) {
                        const errorMsg = data && data.error ? data.error : `Error ${response.status}`;
                        throw new Error(errorMsg);
                    }
                    return data;
                }).catch(error => {
                    // Si el error ya fue lanzado intencionalmente, re-lanzarlo
                    if (error.message && error.message.startsWith('Error')) {
                        throw error;
                    }
                    // Si falla el parseo JSON, leer como texto
                    return response.text().then(text => {
                        throw new Error(`Error ${response.status}: ${text}`);
                    });
                });
            })
            .then(data => {
                ocultarCarga();
                // Verificar explícitamente si la respuesta indica éxito
                if (data && data.success === true) {
                    mostrarMensaje('Éxito', 'Usuario creado exitosamente!', 'success');
                    cerrarModalCrear();
                    setTimeout(() => window.location.reload(), 1500);
                    return; // Salir temprano si fue exitoso
                }
                
                // Si llegamos aquí, hubo un error
                let errorMsg = 'Intenta de nuevo.';
                if (data && data.error) {
                    // Si el error es un string JSON, intentar parsearlo
                    if (typeof data.error === 'string' && data.error.trim().startsWith('{')) {
                        try {
                            const errorObj = JSON.parse(data.error);
                            // Extraer el primer error del objeto
                            const firstKey = Object.keys(errorObj)[0];
                            if (errorObj[firstKey] && Array.isArray(errorObj[firstKey]) && errorObj[firstKey].length > 0) {
                                const firstError = errorObj[firstKey][0];
                                errorMsg = typeof firstError === 'object' && firstError.message 
                                    ? firstError.message 
                                    : String(firstError);
                            }
                        } catch (e) {
                            // Si falla el parseo, usar el string directamente
                            errorMsg = data.error;
                        }
                    } else {
                        errorMsg = String(data.error);
                    }
                }
                mostrarMensaje('Error', 'Error al crear usuario: ' + errorMsg, 'error');
            })
            .catch(error => {
                ocultarCarga();
                console.error("Error detallado:", error.message);
                mostrarMensaje('Error', 'Error al crear usuario: ' + limpiarMensajeError(error.message), 'error');
            });
        });
    }
    console.log("Lógica del modal Crear Usuario inicializada.");

    //SECCION 3: Eliminar Usuario con Modal de Confirmación
    let userIdsToDeleteGlobal = []; // Variable para almacenar los IDs temporalmente

    function abrirModalConfirmarEliminar(userIds, nombres) {
        userIdsToDeleteGlobal = userIds;
        
        // Personalizar mensaje según cantidad
        let mensaje = '';
        if (userIds.length === 1) {
            mensaje = `¿Estás seguro de que deseas eliminar al usuario <strong>${nombres[0]}</strong>?`;
        } else {
            mensaje = `¿Estás seguro de que deseas eliminar <strong>${userIds.length} usuario(s)</strong>?`;
        }
        
        mostrarConfirmacion(
            'Confirmar Eliminación',
            mensaje,
            'Esta acción no se puede deshacer.',
            ejecutarEliminacion,
            'danger'
        );
    }

    // Función para ejecutar la eliminación
    function ejecutarEliminacion() {
        if (userIdsToDeleteGlobal.length === 0) {
            mostrarMensaje('Advertencia', 'No hay usuarios seleccionados para eliminar.', 'warning');
            return;
        }
        
        // Guardar los IDs antes de limpiar la variable
        const userIdsToDelete = [...userIdsToDeleteGlobal];
        userIdsToDeleteGlobal = [];
        
        mostrarCarga('Eliminando usuario(s)...');

        const url = window.ELIMINAR_USUARIOS_URL || '/administrar/eliminar/';
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

        if (!csrfToken) {
            ocultarCarga();
            mostrarMensaje('Error', 'Error de seguridad: No se encontró el token CSRF.', 'error');
            return;
        }

        console.log('Enviando IDs para eliminar:', userIdsToDelete);
        
        fetch(url, {
            method: 'POST', 
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({ user_ids: userIdsToDelete })
        })
        .then(response => {
            return response.json().then(data => {
                if (!response.ok) {
                    // Si el error es por autoeliminación, mostrar el modal de advertencia
                    if (data && data.error && (
                        data.error.includes('No puedes eliminarte a ti mismo') || 
                        data.error.includes('autoeliminarte')
                    )) {
                        ocultarCarga();
                        mostrarMensaje(
                            'Advertencia',
                            '<strong>No puedes autoeliminarte</strong>',
                            'warning',
                            'No puedes eliminar tu propia cuenta de usuario. Si necesitas eliminar tu cuenta, contacta con otro administrador.'
                        );
                        return null;
                    }
                    throw new Error(`Error ${response.status}: ${JSON.stringify(data)}`);
                }
                return data;
            }).catch(error => {
                // Si hay error al parsear JSON, intentar leer como texto
                if (error.message.includes('JSON')) {
                    return response.text().then(text => {
                        throw new Error(`Error ${response.status}: ${text}`);
                    });
                }
                throw error;
            });
        })
        .then(data => {
            if (data === null) return; // Ya se manejó el caso de autoeliminación
            
            ocultarCarga();
            if (data.success) {
                mostrarMensaje(
                    'Éxito',
                    `${data.deleted_count || userIdsToDelete.length} usuario(s) eliminado(s) exitosamente.`,
                    'success'
                );
                setTimeout(() => window.location.reload(), 1500);
            } else {
                // También verificar si el error es por autoeliminación en la respuesta
                if (data.error && data.error.includes('No puedes eliminarte a ti mismo')) {
                    mostrarMensaje(
                        'Advertencia',
                        '<strong>No puedes autoeliminarte</strong>',
                        'warning',
                        'No puedes eliminar tu propia cuenta de usuario. Si necesitas eliminar tu cuenta, contacta con otro administrador.'
                    );
                } else {
                    mostrarMensaje('Error', 'Error al eliminar: ' + (data.error || 'Intenta de nuevo.'), 'error');
                }
            }
        })
        .catch(error => {
            ocultarCarga();
            console.error("Error al eliminar:", error.message);
            mostrarMensaje('Error', 'Error al eliminar usuario: ' + limpiarMensajeError(error.message), 'error');
        });
    }


    // Event listener para el botón eliminar
    if (btnEliminar) {
        btnEliminar.addEventListener('click', function() {
            const selectedCards = document.querySelectorAll('.user-card.selected');
            const userIdsToDelete = Array.from(selectedCards).map(card => card.dataset.userId);
            const nombresUsuarios = Array.from(selectedCards).map(card => {
                const nombreElement = card.querySelector('h4');
                return nombreElement ? nombreElement.textContent.trim() : 'Usuario';
            });

            if (userIdsToDelete.length === 0) {
                mostrarMensaje('Advertencia', 'Selecciona al menos un usuario para eliminar.', 'warning');
                return; 
            }
            
            // Verificar si el usuario intenta eliminarse a sí mismo
            const currentUserId = window.CURRENT_USER_ID;
            if (currentUserId && userIdsToDelete.includes(currentUserId)) {
                mostrarMensaje(
                    'Advertencia',
                    '<strong>No puedes autoeliminarte</strong>',
                    'warning',
                    'No puedes eliminar tu propia cuenta de usuario. Si necesitas eliminar tu cuenta, contacta con otro administrador.'
                );
                return;
            }
            
            abrirModalConfirmarEliminar(userIdsToDelete, nombresUsuarios);
        });
    }

    //SECCION 4: Modal Modificar Usuario
    const modalModificarOverlay = document.getElementById('modificar-usuario-modal-overlay');
    const btnCerrarModificar = document.getElementById('btn-cerrar-modificar-usuario');
    const btnCerrarModificarX = document.getElementById('btn-cerrar-modificar-usuario-x');
    const formModificarUsuario = document.getElementById('form-modificar-usuario');

    function abrirModalModificar() {
        if (!modalModificarOverlay) return;
        const selectedCard = document.querySelector('.user-card.selected');
        if (!selectedCard) {
            mostrarMensaje('Advertencia', 'Selecciona un usuario para modificar.', 'warning');
            return;
        }

        // Usar data-* attributes para extracción robusta
        const userId = selectedCard.dataset.userId;
        const nombre = selectedCard.dataset.nombre;
        const correo = selectedCard.dataset.correo;
        const rol = selectedCard.dataset.rol === 'true';

        document.getElementById('modificar-user-id').value = userId;
        document.getElementById('modificar-nombre').value = nombre;
        document.getElementById('modificar-correo').value = correo;
        document.getElementById('modificar-rol').checked = rol;

        modalModificarOverlay.style.display = 'flex';
    }

    function cerrarModalModificar() {
        if (!modalModificarOverlay) return;
        modalModificarOverlay.style.display = 'none';
    }

    if (btnModificar) btnModificar.addEventListener('click', abrirModalModificar);
    if (btnCerrarModificar) btnCerrarModificar.addEventListener('click', cerrarModalModificar);
    if (btnCerrarModificarX) btnCerrarModificarX.addEventListener('click', cerrarModalModificar);
    // Event listener para cerrar modal al hacer clic fuera eliminado por solicitud del usuario

    if (formModificarUsuario) {
        formModificarUsuario.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // Validación del lado del cliente para contraseñas
            const contrasena = document.getElementById('modificar-contrasena').value;
            const confirmarContrasena = document.getElementById('modificar-confirmar-contrasena').value;
            
            // Si se proporciona contraseña, validar
            if (contrasena && contrasena.trim() !== '') {
                // Verificar que las contraseñas coincidan
                if (contrasena !== confirmarContrasena) {
                    mostrarMensaje('Error', 'Las contraseñas no coinciden. Por favor, verifique que ambas sean iguales.', 'error');
                    return;
                }
                
                // Verificar requisitos de la contraseña
                const errores = [];
                if (contrasena.length < 8) {
                    errores.push('La contraseña debe tener al menos 8 caracteres.');
                }
                if (!/[A-Z]/.test(contrasena)) {
                    errores.push('La contraseña debe contener al menos una letra mayúscula.');
                }
                if (!/[a-z]/.test(contrasena)) {
                    errores.push('La contraseña debe contener al menos una letra minúscula.');
                }
                if (!/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(contrasena)) {
                    errores.push('La contraseña debe contener al menos un símbolo especial (!@#$%^&*()_+-=[]{}|;:,.<>?).');
                }
                
                if (errores.length > 0) {
                    mostrarMensaje('Error de validación', errores.join('\n'), 'error');
                    return;
                }
            } else if (confirmarContrasena && confirmarContrasena.trim() !== '') {
                // Si se proporciona confirmación pero no contraseña, es un error
                mostrarMensaje('Error', 'Debe ingresar la nueva contraseña si desea cambiarla.', 'error');
                return;
            }
            
            mostrarCarga('Modificando usuario...');
            console.log("[Modificar] Enviando formulario...");

            const formData = new FormData(formModificarUsuario);
            if (!formData.has('rol')) {
                formData.append('rol', 'false');
            } else {
                formData.set('rol', 'true');
            }

            const url = formModificarUsuario.action;
            const csrf = formData.get('csrfmiddlewaretoken');

            fetch(url, {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': csrf }
            })
            .then(async response => {
                const text = await response.text();
                let json = null;
                try { 
                    json = JSON.parse(text); 
                } catch(e) {}
                if (!response.ok) {
                    const msg = (json && (json.error || JSON.stringify(json))) || text || response.statusText;
                    throw new Error(`HTTP ${response.status}: ${msg}`);
                }
                return json || {};
            })
            .then(data => {
                ocultarCarga();
                if (data.success) {
                    mostrarMensaje('Éxito', 'Usuario modificado exitosamente.', 'success');
                    cerrarModalModificar();
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    mostrarMensaje('Error', 'No se pudo modificar: ' + (data.error || 'Error desconocido.'), 'error');
                }
            })
            .catch(error => {
                ocultarCarga();
                console.error("Error al modificar:", error.message);
                mostrarMensaje('Error', 'Error al modificar usuario: ' + limpiarMensajeError(error.message), 'error');
            });
        });
    }

    // ========== VALIDACIÓN DE CAMPOS NUMÉRICOS Y DE TEXTO ==========
    function inicializarValidacionCampos() {
        // Validar campos numéricos: solo permitir números, punto decimal y signo negativo
        document.querySelectorAll('input[type="number"]').forEach(function(input) {
            // Prevenir caracteres no numéricos al escribir
            input.addEventListener('keydown', function(e) {
                const key = e.key;
                const value = this.value;
                const cursorPos = this.selectionStart;
                
                // Permitir teclas de control (backspace, delete, tab, escape, enter, etc.)
                if (['Backspace', 'Delete', 'Tab', 'Escape', 'Enter', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(key)) {
                    return;
                }
                
                // Permitir (copiar, pegar, cortar, seleccionar todo)
                if (e.ctrlKey || e.metaKey) {
                    if (['a', 'c', 'v', 'x'].includes(key.toLowerCase())) {
                        return;
                    }
                }
                
                // Permitir números
                if (key >= '0' && key <= '9') {
                    return;
                }
                
                // Permitir punto decimal solo si no existe ya uno
                if (key === '.' || key === ',') {
                    const decimalChar = this.step && this.step.toString().includes('.') ? '.' : '.';
                    if (value.indexOf(decimalChar) === -1) {
                        // Si se presiona coma, convertirla a punto
                        if (key === ',') {
                            e.preventDefault();
                            const newValue = value.substring(0, cursorPos) + '.' + value.substring(cursorPos);
                            this.value = newValue;
                            this.setSelectionRange(cursorPos + 1, cursorPos + 1);
                        }
                        return;
                    }
                }
                
                // Permitir signo negativo solo al inicio
                if (key === '-' && cursorPos === 0 && value.indexOf('-') === -1) {
                    return;
                }
                
                // Bloquear cualquier otro carácter
                e.preventDefault();
            });
            
            // Validar al pegar contenido
            input.addEventListener('paste', function(e) {
                e.preventDefault();
                const pastedText = (e.clipboardData || window.clipboardData).getData('text');
                const currentValue = this.value;
                const cursorPos = this.selectionStart;
                const selectionEnd = this.selectionEnd;
                
                // Limpiar el texto pegado: solo números, punto decimal y signo negativo
                let cleanedText = pastedText.replace(/[^0-9.\-]/g, '');
                
                // Asegurar que solo haya un punto decimal
                const parts = cleanedText.split('.');
                if (parts.length > 2) {
                    cleanedText = parts[0] + '.' + parts.slice(1).join('');
                }
                
                // Asegurar que el signo negativo solo esté al inicio
                if (cleanedText.includes('-')) {
                    cleanedText = cleanedText.replace(/-/g, '');
                    if (cursorPos === 0 && !currentValue.startsWith('-')) {
                        cleanedText = '-' + cleanedText;
                    }
                }
                
                // Insertar el texto limpio
                const newValue = currentValue.substring(0, cursorPos) + cleanedText + currentValue.substring(selectionEnd);
                this.value = newValue;
                this.setSelectionRange(cursorPos + cleanedText.length, cursorPos + cleanedText.length);
            });
        });
        
        // Validar campos de texto: mostrar advertencia si contienen solo números
        document.querySelectorAll('input[type="text"]:not([readonly]):not([data-allow-numbers])').forEach(function(input) {
            // Validar al escribir: mostrar advertencia visual si el campo contiene solo números
            input.addEventListener('input', function() {
                const value = this.value.trim();
                // Si el campo contiene solo números, cambiar el color del borde a advertencia
                if (value && /^\d+$/.test(value)) {
                    this.style.borderColor = '#ffaa00';
                    this.title = 'Advertencia: Este campo no debería contener solo números';
                } else {
                    this.style.borderColor = '';
                    this.title = '';
                }
            });
            
            // Validar al perder el foco: mostrar notificación si contiene solo números
            input.addEventListener('blur', function() {
                const value = this.value.trim();
                if (value && /^\d+$/.test(value)) {
                    this.style.borderColor = '#ffaa00';
                    mostrarNotificacion('Advertencia: Los campos de texto no deberían contener solo números.', 'warning');
                }
            });
        });
    }
    
    // Inicializar validación de campos
    inicializarValidacionCampos();
    
    // Re-inicializar validación cuando se abren modales (porque se crean dinámicamente)
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) {
                        // Si se agregó un modal o un contenedor de formulario, re-inicializar validación
                        if (node.classList && (node.classList.contains('modal-overlay') || node.querySelector('input[type="number"], input[type="text"]'))) {
                            setTimeout(inicializarValidacionCampos, 100);
                        }
                    }
                });
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    console.log("Script completo cargado y listeners asignados.");  
});

