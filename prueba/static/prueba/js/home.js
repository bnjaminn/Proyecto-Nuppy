/**
 * HOME.JS - JavaScript Principal del Dashboard
 * ============================================
 * 
 * POR QUÉ ESTE SCRIPT ES CRÍTICO:
 * - Es el corazón de la funcionalidad del dashboard
 * - Maneja todas las operaciones CRUD de calificaciones
 * - Calcula factores financieros desde montos (lógica de negocio crítica)
 * - Permite carga masiva de datos desde CSV
 * - Proporciona búsqueda y filtrado dinámico
 * - Gestiona modales complejos para ingreso y edición
 * 
 * CÓMO FUNCIONA:
 * 1. Al cargar la página, inicializa todos los event listeners
 * 2. Carga calificaciones desde el servidor y las muestra en la tabla
 * 3. Permite abrir modales para crear/editar calificaciones
 * 4. Calcula factores financieros en tiempo real desde montos
 * 5. Maneja carga masiva de CSV con previsualización
 * 6. Permite buscar, filtrar, exportar, eliminar y copiar calificaciones
 * 7. Muestra logs de auditoría para cada calificación
 * 
 * FUNCIONALIDADES PRINCIPALES:
 * - Modales de ingreso y edición de calificaciones (dos modales: datos básicos + factores)
 * - Cálculo de factores desde montos (Fórmula: Factor = Monto / SumaBase)
 * - Búsqueda y filtrado de calificaciones (por mercado, origen, período)
 * - Carga masiva de archivos CSV (factores y montos con previsualización)
 * - Modificación, eliminación y copia de calificaciones
 * - Visualización de logs de cambios (auditoría)
 * - Exportación de calificaciones a CSV
 * - Gestión de tema oscuro/claro
 * 
 * CÁLCULOS FINANCIEROS:
 * - SumaBase = suma de montos del 8 al 19
 * - Factor = Monto / SumaBase (para cada monto del 8 al 37)
 * - Precisión: 8 decimales usando Decimal para evitar errores de punto flotante
 * ============================================
 */

// ============================================
// FUNCIÓN AUXILIAR: getCookie(name)
// ============================================
/**
 * Obtiene el valor de una cookie específica por su nombre.
 * 
 * POR QUÉ ESTA FUNCIÓN ES NECESARIA:
 * - Las cookies se almacenan en document.cookie como un string único
 * - Necesitamos extraer el valor de una cookie específica
 * - Se usa principalmente para obtener el token CSRF de Django
 * - El token CSRF es requerido para todas las peticiones POST/PUT/DELETE
 * - Previene ataques CSRF (Cross-Site Request Forgery)
 * 
 * CÓMO FUNCIONA:
 * 1. Verifica que existan cookies en el documento
 * 2. Divide todas las cookies por el separador ';'
 * 3. Busca la cookie que coincida con el nombre proporcionado
 * 4. Extrae y decodifica el valor de la cookie
 * 5. Retorna el valor o null si no se encuentra
 * 
 * Parámetros:
 *   - name (string): Nombre de la cookie que se desea obtener
 * 
 * Retorna:
 *   - string | null: El valor de la cookie si existe, o null si no se encuentra
 * 
 * Ejemplo de uso:
 *   const csrfToken = getCookie('csrftoken');
 */
function getCookie(name) {
    // Inicializar variable para almacenar el valor de la cookie
    // POR QUÉ: Necesitamos una variable para guardar el valor encontrado
    // CÓMO: Se inicializa en null y se actualiza si se encuentra la cookie
    let cookieValue = null;
    
    // Verificar que existen cookies en el documento
    // POR QUÉ: Si no hay cookies, no tiene sentido buscar
    // CÓMO: document.cookie contiene todas las cookies como un string
    // LÓGICA: Si document.cookie está vacío o es null, no hay cookies
    if (document.cookie && document.cookie !== '') {
        // Dividir todas las cookies por el separador ';'
        // POR QUÉ: Las cookies vienen en formato: "cookie1=valor1; cookie2=valor2; cookie3=valor3"
        // CÓMO: split(';') divide el string en un array de strings
        // LÓGICA: Cada elemento del array es una cookie en formato "nombre=valor"
        const cookies = document.cookie.split(';');
        
        // Buscar la cookie que coincida con el nombre proporcionado
        // POR QUÉ: Necesitamos iterar sobre todas las cookies para encontrar la correcta
        // CÓMO: for loop itera sobre cada cookie en el array
        for (let i = 0; i < cookies.length; i++) {
            // Limpiar espacios en blanco alrededor de la cookie
            // POR QUÉ: Los espacios pueden causar problemas al comparar
            // CÓMO: trim() elimina espacios al inicio y final del string
            // LÓGICA: " cookie=valor " se convierte en "cookie=valor"
            const cookie = cookies[i].trim();
            
            // Verificar si esta cookie comienza con el nombre buscado seguido de '='
            // POR QUÉ: Las cookies tienen formato "nombre=valor", necesitamos verificar el nombre
            // CÓMO: substring(0, name.length + 1) obtiene los primeros caracteres (nombre + '=')
            // LÓGICA: Si buscamos 'csrftoken', verificamos si la cookie es 'csrftoken=valor...'
            // Ejemplo: cookie.substring(0, 9) de "csrftoken=abc123" es "csrftoken="
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                // Extraer el valor después del '=' y decodificarlo
                // POR QUÉ: El valor puede tener caracteres especiales codificados (ej: espacios como %20)
                // CÓMO: substring(name.length + 1) obtiene todo después del '='
                // decodeURIComponent() decodifica caracteres especiales (ej: %20 → espacio)
                // LÓGICA: "csrftoken=abc123" → substring(10) → "abc123"
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                
                // Salir del bucle porque ya encontramos la cookie
                // POR QUÉ: No necesitamos seguir buscando si ya la encontramos
                // CÓMO: break sale inmediatamente del bucle for
                break;
            }
        }
    }
    
    // Retornar el valor de la cookie encontrada o null
    // POR QUÉ: Si no se encontró la cookie, retornamos null
    // CÓMO: return sale de la función y devuelve el valor
    return cookieValue;
}

// ============================================
// TOKEN CSRF
// ============================================
// Obtener el token CSRF necesario para todas las peticiones AJAX POST/PUT/DELETE.
// Django requiere este token en todas las peticiones que modifican datos para prevenir
// ataques de Cross-Site Request Forgery (CSRF).
// 
// Este token se envía en el header 'X-CSRFToken' de cada petición fetch.
// ============================================
const csrftoken = getCookie('csrftoken');

// ============================================
// FUNCIONES PARA MODAL DE MENSAJES
// ============================================
// Estas funciones permiten mostrar mensajes informativos al usuario en un modal reutilizable.
// Se pueden mostrar mensajes simples (con un solo botón) o confirmaciones (con dos botones).

// ============================================
// FUNCIÓN: mostrarMensaje(titulo, mensaje, tipo, advertencia)
// ============================================
// Propósito: Muestra un mensaje simple en un modal con un solo botón "Aceptar".
// 
// Parámetros:
//   - titulo (string): Título del modal (ej: "Éxito", "Error", "Información")
//   - mensaje (string): Mensaje principal a mostrar (puede contener HTML)
//   - tipo (string, opcional): Tipo de mensaje ('success', 'error', 'warning', 'info')
//     - 'success': Mensaje de éxito (verde, icono ✓)
//     - 'error': Mensaje de error (rojo, icono ✕)
//     - 'warning': Mensaje de advertencia (amarillo, icono ⚠)
//     - 'info': Mensaje informativo (azul, icono ℹ) - por defecto
//   - advertencia (string, opcional): Mensaje de advertencia adicional a mostrar debajo del mensaje principal
// 
// Retorna: void (no retorna nada, solo muestra el modal)
// 
// Ejemplo de uso:
//   mostrarMensaje('Éxito', 'Usuario creado correctamente', 'success');
//   mostrarMensaje('Error', 'No se pudo guardar', 'error', 'Verifique su conexión');
// ============================================
function mostrarMensaje(titulo, mensaje, tipo = 'info', advertencia = null) {
    // ========== OBTENER REFERENCIAS A TODOS LOS ELEMENTOS DEL MODAL ==========
    // Buscar el elemento del overlay del modal usando su ID 'mensaje-modal-overlay'
    // getElementById busca un elemento en el documento con el ID especificado
    const modalMensaje = document.getElementById('mensaje-modal-overlay');
    // Buscar el elemento del título del modal usando su ID 'mensaje-modal-titulo'
    // Este elemento mostrará el título del mensaje
    const tituloMensaje = document.getElementById('mensaje-modal-titulo');
    // Buscar el elemento del texto del mensaje usando su ID 'mensaje-modal-texto'
    // Este elemento mostrará el contenido principal del mensaje
    const textoMensaje = document.getElementById('mensaje-modal-texto');
    // Buscar el elemento del icono del modal usando su ID 'mensaje-modal-icono'
    // Este elemento mostrará el icono visual según el tipo de mensaje
    const iconoMensaje = document.getElementById('mensaje-modal-icono');
    // Buscar el elemento de advertencia del modal usando su ID 'mensaje-modal-advertencia'
    // Este elemento es opcional y puede mostrar un mensaje de advertencia adicional
    // Puede ser null si el elemento no existe en el DOM
    const advertenciaMensaje = document.getElementById('mensaje-modal-advertencia');
    // Buscar el botón de cerrar usando su ID 'btn-cerrar-mensaje'
    // Este botón se usa en modo simple para cerrar el modal
    // Puede ser null si el elemento no existe en el DOM
    const btnCerrar = document.getElementById('btn-cerrar-mensaje');
    // Buscar el botón de cancelar usando su ID 'btn-cancelar-mensaje'
    // Este botón se usa en modo confirmación para cancelar la acción
    // Puede ser null si el elemento no existe en el DOM
    const btnCancelar = document.getElementById('btn-cancelar-mensaje');
    // Buscar el botón de confirmar usando su ID 'btn-confirmar-mensaje'
    // Este botón se usa en modo confirmación para confirmar la acción
    // Puede ser null si el elemento no existe en el DOM
    const btnConfirmar = document.getElementById('btn-confirmar-mensaje');
    
    // ========== VALIDAR QUE LOS ELEMENTOS ESENCIALES EXISTAN ==========
    // Verificar que los elementos críticos del modal existan antes de continuar
    // Usar operador lógico OR (||) para verificar si alguno es null, undefined o falsy
    // Si alguno de los elementos esenciales no existe, salir de la función con return
    // Esto previene errores de JavaScript si los elementos no están en el DOM
    if (!modalMensaje || !tituloMensaje || !textoMensaje || !iconoMensaje) return;
    
    // ========== CONFIGURAR CONTENIDO DEL MODAL ==========
    
    // Asignar el valor del parámetro 'titulo' al contenido de texto del elemento título
    // Usar textContent en lugar de innerHTML para evitar interpretación de HTML
    // textContent escapa automáticamente cualquier HTML que pudiera contener el título
    tituloMensaje.textContent = titulo;
    
    // Asignar el valor del parámetro 'mensaje' al contenido HTML del elemento mensaje
    // Usar innerHTML en lugar de textContent para permitir HTML básico como <br>, <strong>, etc.
    // Esto permite formateo básico del mensaje si es necesario
    // NOTA: innerHTML puede ser vulnerable a XSS si el contenido no es confiable
    textoMensaje.innerHTML = mensaje;
    
    // ========== CONFIGURAR MENSAJE DE ADVERTENCIA ADICIONAL (OPCIONAL) ==========
    // Verificar si el elemento de advertencia existe antes de intentar usarlo
    // Esto previene errores si el elemento no está presente en el DOM
    if (advertenciaMensaje) {
        // Verificar si se proporcionó un mensaje de advertencia (no es null ni undefined)
        // El parámetro 'advertencia' puede ser null, undefined o un string
        if (advertencia) {
            // Si se proporciona una advertencia, asignar su valor al contenido de texto del elemento
            // Usar textContent para evitar interpretación de HTML (por seguridad)
            advertenciaMensaje.textContent = advertencia;
            // Mostrar el elemento de advertencia cambiando su propiedad display a 'block'
            // 'block' hace que el elemento sea visible y ocupe todo el ancho disponible
            advertenciaMensaje.style.display = 'block';
        } else {
            // Si no hay advertencia (es null o undefined), ocultar el elemento
            // Cambiar la propiedad display a 'none' para ocultar el elemento
            // 'none' hace que el elemento no sea visible y no ocupe espacio en el DOM
            advertenciaMensaje.style.display = 'none';
        }
    }
    
    // ========== CONFIGURAR ICONO Y COLOR SEGÚN EL TIPO ==========
    // Usar una estructura switch para determinar qué icono y color usar según el tipo
    // El switch evalúa el valor del parámetro 'tipo' y ejecuta el caso correspondiente
    // Cada tipo de mensaje tiene un icono y color de fondo diferentes para mejor UX
    switch(tipo) {
        case 'success':
            // Si el tipo es 'success' (éxito), ejecutar este bloque de código
            // Usar Bootstrap Icon de check
            iconoMensaje.innerHTML = '<i class="bi bi-check-circle-fill"></i>';
            // Asignar un gradiente verde como fondo del icono usando la propiedad style.background
            // linear-gradient crea un gradiente lineal con los colores especificados
            // 135deg es el ángulo del gradiente (diagonal de arriba-izquierda a abajo-derecha)
            // #28A745 y #20C997 son los colores verde claro y verde oscuro del gradiente
            iconoMensaje.style.background = 'linear-gradient(135deg, #28A745 0%, #20C997 100%)';
            // Salir del switch con break para evitar ejecutar los demás casos
            break;
        case 'error':
            // Si el tipo es 'error', ejecutar este bloque de código
            // Usar Bootstrap Icon de X
            iconoMensaje.innerHTML = '<i class="bi bi-x-circle-fill"></i>';
            // Asignar un gradiente rojo como fondo del icono
            // #DC3545 y #C82333 son los colores rojo claro y rojo oscuro del gradiente
            iconoMensaje.style.background = 'linear-gradient(135deg, #DC3545 0%, #C82333 100%)';
            // Salir del switch con break para evitar ejecutar los demás casos
            break;
        case 'warning':
            // Si el tipo es 'warning' (advertencia), ejecutar este bloque de código
            // Usar Bootstrap Icon de advertencia
            iconoMensaje.innerHTML = '<i class="bi bi-exclamation-triangle-fill"></i>';
            // Asignar un gradiente amarillo/naranja como fondo del icono
            // #FFC107 y #FF9800 son los colores amarillo y naranja del gradiente
            iconoMensaje.style.background = 'linear-gradient(135deg, #FFC107 0%, #FF9800 100%)';
            // Salir del switch con break para evitar ejecutar los demás casos
            break;
        default: // info
            // Si el tipo es 'info' o cualquier otro valor (caso por defecto), ejecutar este bloque
            // El caso default se ejecuta si ningún otro caso coincide con el valor de 'tipo'
            // Usar Bootstrap Icon de información
            iconoMensaje.innerHTML = '<i class="bi bi-info-circle-fill"></i>';
            // Asignar un gradiente azul como fondo del icono
            // #17A2B8 y #138496 son los colores azul claro y azul oscuro del gradiente
            iconoMensaje.style.background = 'linear-gradient(135deg, #17A2B8 0%, #138496 100%)';
    }
    
    // ========== CONFIGURAR BOTONES (MODO SIMPLE: UN SOLO BOTÓN) ==========
    // En modo simple, solo se muestra el botón "Aceptar"
    // Los botones de cancelar y confirmar se ocultan (son para modo confirmación)
    
    // Verificar si el botón cerrar existe antes de modificarlo
    // Esto previene errores si el elemento no está presente en el DOM
    if (btnCerrar) {
        // Mostrar el botón cerrar cambiando su propiedad display a 'inline-block'
        // 'inline-block' hace que el botón sea visible y mantenga su forma de elemento inline
        // Esto permite que el botón se muestre en línea con otros elementos
        btnCerrar.style.display = 'inline-block';
    }
    // Verificar si el botón cancelar existe antes de modificarlo
    if (btnCancelar) {
        // Ocultar el botón cancelar cambiando su propiedad display a 'none'
        // 'none' hace que el botón no sea visible y no ocupe espacio en el DOM
        btnCancelar.style.display = 'none';
    }
    // Verificar si el botón confirmar existe antes de modificarlo
    if (btnConfirmar) {
        // Ocultar el botón confirmar cambiando su propiedad display a 'none'
        // 'none' hace que el botón no sea visible y no ocupe espacio en el DOM
        btnConfirmar.style.display = 'none';
    }
    
    // ========== LIMPIAR EVENT LISTENERS ==========
    // Clonar el botón confirmar para eliminar event listeners anteriores
    // Esto previene que se acumulen múltiples listeners si se abre el modal varias veces
    // Verificar si el botón confirmar existe antes de intentar clonarlo
    if (btnConfirmar) {
        // Clonar el botón confirmar incluyendo todos sus atributos y estructura
        // cloneNode(true) crea una copia profunda del elemento (incluye todos los hijos)
        // El parámetro 'true' indica clonación profunda, 'false' sería clonación superficial
        // Esto crea un nuevo elemento sin los event listeners asociados al original
        const nuevoBtnConfirmar = btnConfirmar.cloneNode(true);
        // Reemplazar el botón original con el clon en el DOM
        // parentNode devuelve el nodo padre del elemento
        // replaceChild requiere tres parámetros: nuevoNodo, viejoNodo
        // Esto elimina los event listeners anteriores que puedan estar acumulados
        btnConfirmar.parentNode.replaceChild(nuevoBtnConfirmar, btnConfirmar);
    }
    
    // ========== MOSTRAR EL MODAL ==========
    // Cambiar el display del modal a 'flex' para mostrarlo
    // El valor 'flex' activa el modelo de caja flexbox y hace visible el modal con su overlay
    // 'flex' permite centrar el contenido del modal fácilmente usando flexbox
    modalMensaje.style.display = 'flex';
}

// ============================================
// FUNCIÓN: mostrarConfirmacion(titulo, mensaje, advertencia, onConfirmar, tipoBotonConfirmar, textoBotonConfirmar)
// ============================================
// Propósito: Muestra un modal de confirmación con dos botones: "Cancelar" y "Confirmar".
// Se usa para confirmar acciones importantes antes de ejecutarlas (ej: eliminar, copiar).
// 
// Parámetros:
//   - titulo (string): Título del modal de confirmación
//   - mensaje (string): Mensaje principal a mostrar (puede contener HTML)
//   - advertencia (string | null): Mensaje de advertencia adicional (ej: "Esta acción no se puede deshacer")
//   - onConfirmar (function): Función callback que se ejecuta cuando el usuario presiona "Confirmar"
//   - tipoBotonConfirmar (string, opcional): Tipo de botón confirmar ('danger' o 'primary')
//     - 'danger': Botón rojo (para acciones destructivas como eliminar)
//     - 'primary': Botón normal (para otras confirmaciones)
//   - textoBotonConfirmar (string | null, opcional): Texto personalizado para el botón confirmar
//     Si es null, usa 'Eliminar' para tipo 'danger' o 'Confirmar' para otros tipos
// 
// Retorna: void (no retorna nada, solo muestra el modal)
// 
// Ejemplo de uso:
//   mostrarConfirmacion(
//       'Confirmar Eliminación',
//       '¿Estás seguro de que deseas eliminar esta calificación?',
//       'Esta acción no se puede deshacer.',
//       function() { eliminarCalificacion(id); },
//       'danger'
//   );
// ============================================
function mostrarConfirmacion(titulo, mensaje, advertencia, onConfirmar, tipoBotonConfirmar = 'danger', textoBotonConfirmar = null) {
    // Obtener referencias a todos los elementos del modal
    const modalMensaje = document.getElementById('mensaje-modal-overlay');
    const tituloMensaje = document.getElementById('mensaje-modal-titulo');
    const textoMensaje = document.getElementById('mensaje-modal-texto');
    const iconoMensaje = document.getElementById('mensaje-modal-icono');
    const advertenciaMensaje = document.getElementById('mensaje-modal-advertencia');
    const btnCerrar = document.getElementById('btn-cerrar-mensaje');
    const btnCancelar = document.getElementById('btn-cancelar-mensaje');
    const btnConfirmar = document.getElementById('btn-confirmar-mensaje');
    
    // Validar que los elementos esenciales existan antes de continuar
    if (!modalMensaje || !tituloMensaje || !textoMensaje || !iconoMensaje) return;
    
    // ========== CONFIGURAR CONTENIDO DEL MODAL ==========
    
    // Establecer el título y mensaje principal
    tituloMensaje.textContent = titulo;
    textoMensaje.innerHTML = mensaje;
    
    // Configurar mensaje de advertencia (si se proporciona)
    if (advertenciaMensaje) {
        if (advertencia) {
            advertenciaMensaje.textContent = advertencia;
            advertenciaMensaje.style.display = 'block';
        } else {
            advertenciaMensaje.style.display = 'none';
        }
    }
    
    // ========== CONFIGURAR ICONO (SIEMPRE ADVERTENCIA) ==========
    // Los modales de confirmación siempre usan el icono de advertencia
    iconoMensaje.innerHTML = '<i class="bi bi-exclamation-triangle-fill"></i>';
    iconoMensaje.style.background = 'linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%)';
    
    // ========== CONFIGURAR BOTONES (MODO CONFIRMACIÓN: DOS BOTONES) ==========
    // En modo confirmación, se muestran dos botones: Cancelar y Confirmar
    // El botón de cerrar simple se oculta
    
    // Ocultar botón de cerrar simple
    if (btnCerrar) btnCerrar.style.display = 'none';
    
    // Mostrar botón de cancelar
    if (btnCancelar) btnCancelar.style.display = 'inline-block';
    
    // Configurar botón de confirmar
    if (btnConfirmar) {
        // Mostrar el botón
        btnConfirmar.style.display = 'inline-block';
        
        // Configurar estilo del botón según el tipo
        // - 'danger': Botón rojo (para acciones destructivas)
        // - Otros: Botón normal
        if (tipoBotonConfirmar === 'danger') {
            btnConfirmar.className = 'btn btn-danger-modal';
        } else {
            btnConfirmar.className = 'btn';
        }
        
        // Configurar texto del botón
        // Si se proporciona texto personalizado, usarlo
        // Si no, usar texto por defecto según el tipo
        if (textoBotonConfirmar) {
            btnConfirmar.textContent = textoBotonConfirmar;
        } else {
            // Texto por defecto: 'Eliminar' para danger, 'Confirmar' para otros
            btnConfirmar.textContent = tipoBotonConfirmar === 'danger' ? 'Eliminar' : 'Confirmar';
        }
        
        // Agregar event listener al botón confirmar
        // Cuando se hace clic, cierra el modal y ejecuta la función callback
        btnConfirmar.onclick = function() {
            cerrarModalMensaje(); // Cerrar el modal primero
            if (onConfirmar) onConfirmar(); // Ejecutar la función de confirmación
        };
    }
    
    // ========== MOSTRAR EL MODAL ==========
    modalMensaje.style.display = 'flex';
}

// ============================================
// FUNCIÓN: cerrarModalMensaje()
// ============================================
// Propósito: Cierra el modal de mensajes ocultándolo.
// 
// Flujo:
//   1. Obtiene la referencia al modal
//   2. Cambia su display a 'none' para ocultarlo
// 
// Retorna: void
// 
// Ejemplo de uso:
//   cerrarModalMensaje();
// ============================================
function cerrarModalMensaje() {
    // Buscar el elemento del overlay del modal usando su ID 'mensaje-modal-overlay'
    // getElementById busca un elemento en el documento con el ID especificado
    // Este método devuelve el elemento si existe, o null si no existe
    const modalMensaje = document.getElementById('mensaje-modal-overlay');
    // Verificar si el elemento del modal existe antes de intentar modificarlo
    // Esto previene errores de JavaScript si el elemento no está en el DOM
    if (modalMensaje) {
        // Ocultar el modal cambiando su propiedad display a 'none'
        // 'none' hace que el elemento no sea visible y no ocupe espacio en el DOM
        // Esto efectivamente cierra el modal y permite que el usuario vea el contenido detrás
        modalMensaje.style.display = 'none';
    }
}

// ============================================
// FUNCIÓN: inicializarModalMensaje()
// ============================================
// Propósito: Configura los event listeners para todos los botones que cierran el modal de mensajes.
// 
// Flujo de ejecución:
//   1. Obtiene referencias a todos los botones de cerrar
//   2. Agrega event listeners a cada botón para que llame a cerrarModalMensaje() al hacer clic
// 
// Botones configurados:
//   - btn-cerrar-mensaje: Botón "Aceptar" del modo simple
//   - btn-cancelar-mensaje: Botón "Cancelar" del modo confirmación
//   - btn-cerrar-mensaje-x: Botón X en la esquina superior derecha del modal
// 
// Nota: El event listener para cerrar al hacer clic fuera del modal fue eliminado
//       por solicitud del usuario para evitar cierres accidentales.
// 
// Retorna: void
// 
// Llamada: Se ejecuta automáticamente cuando se carga el DOM (DOMContentLoaded)
// ============================================
function inicializarModalMensaje() {
    // ========== OBTENER REFERENCIAS A TODOS LOS BOTONES DE CERRAR ==========
    // Buscar el botón de cerrar usando su ID 'btn-cerrar-mensaje'
    // Este botón es el botón "Aceptar" que se usa en modo simple
    // getElementById devuelve el elemento si existe, o null si no existe
    const btnCerrarMensaje = document.getElementById('btn-cerrar-mensaje');
    // Buscar el botón de cancelar usando su ID 'btn-cancelar-mensaje'
    // Este botón es el botón "Cancelar" que se usa en modo confirmación
    // Puede ser null si el elemento no existe en el DOM
    const btnCancelarMensaje = document.getElementById('btn-cancelar-mensaje');
    // Buscar el botón X usando su ID 'btn-cerrar-mensaje-x'
    // Este botón está en la esquina superior derecha del modal
    // Puede ser null si el elemento no existe en el DOM
    const btnCerrarMensajeX = document.getElementById('btn-cerrar-mensaje-x');
    // Buscar el overlay del modal usando su ID 'mensaje-modal-overlay'
    // Este elemento es el contenedor principal del modal
    // Puede ser null si el elemento no existe en el DOM
    const modalMensajeOverlay = document.getElementById('mensaje-modal-overlay');
    
    // ========== CONFIGURAR EVENT LISTENERS PARA TODOS LOS BOTONES DE CERRAR ==========
    
    // Configurar event listener para el botón "Aceptar" (modo simple)
    // Verificar si el botón existe antes de agregar el listener
    if (btnCerrarMensaje) {
        // Agregar un event listener al botón para el evento 'click'
        // addEventListener toma dos parámetros: tipo de evento y función callback
        // Cuando el usuario hace clic en el botón, se ejecuta la función cerrarModalMensaje
        // Esto permite cerrar el modal al presionar el botón "Aceptar"
        btnCerrarMensaje.addEventListener('click', cerrarModalMensaje);
    }
    
    // Configurar event listener para el botón "Cancelar" (modo confirmación)
    // Verificar si el botón existe antes de agregar el listener
    if (btnCancelarMensaje) {
        // Agregar un event listener al botón para el evento 'click'
        // Cuando el usuario hace clic en "Cancelar", se cierra el modal sin ejecutar acción
        // Esto permite cancelar la acción en modo confirmación
        btnCancelarMensaje.addEventListener('click', cerrarModalMensaje);
    }
    
    // Configurar event listener para el botón X (esquina superior derecha)
    // Verificar si el botón existe antes de agregar el listener
    if (btnCerrarMensajeX) {
        // Agregar un event listener al botón X para el evento 'click'
        // Cuando el usuario hace clic en la X, se cierra el modal
        // Esto proporciona una forma intuitiva de cerrar el modal
        btnCerrarMensajeX.addEventListener('click', cerrarModalMensaje);
    }
    
    // Nota: Event listener para cerrar modal al hacer clic fuera eliminado por solicitud del usuario
    //       para evitar cierres accidentales del modal.
}

// Hacer las funciones disponibles globalmente
window.mostrarMensaje = mostrarMensaje;
window.mostrarConfirmacion = mostrarConfirmacion;
window.cerrarModalMensaje = cerrarModalMensaje;
window.inicializarModalMensaje = inicializarModalMensaje;

// Esperar a que el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // ========== MODAL DE MENSAJES ==========
    inicializarModalMensaje();
    
    // ========== CALENDARIO DE AÑO PARA PERIODO COMERCIAL ==========
    (function() {
        const periodoInput = document.getElementById('periodo');
        const periodoIcon = document.getElementById('periodo-calendar-icon');
        const periodoPicker = document.getElementById('periodo-year-picker');
        const periodoYearDisplay = document.getElementById('periodo-year-display');
        const periodoYearGrid = document.getElementById('periodo-year-grid');
        const periodoYearPrev = document.getElementById('periodo-year-prev');
        const periodoYearNext = document.getElementById('periodo-year-next');
        
        if (!periodoInput || !periodoIcon || !periodoPicker) return;
        
        let currentDecade = Math.floor(parseInt(periodoInput.value || new Date().getFullYear()) / 10) * 10;
        
        // Función para generar la grilla de años
        function generarGrillaAnos(decadeStart) {
            periodoYearGrid.innerHTML = '';
            periodoYearDisplay.textContent = decadeStart + ' - ' + (decadeStart + 9);
            
            for (let i = 0; i < 10; i++) {
                const year = decadeStart + i;
                const yearButton = document.createElement('button');
                yearButton.type = 'button';
                yearButton.textContent = year;
                yearButton.style.cssText = 'padding: 0.75rem; border: 1px solid var(--border); border-radius: 4px; background: var(--bg-secondary); color: var(--text-primary); cursor: pointer; transition: all 0.2s; font-size: 0.9rem;';
                
                // Resaltar el año actual si coincide
                const currentYear = parseInt(periodoInput.value) || new Date().getFullYear();
                if (year === currentYear) {
                    yearButton.style.background = 'var(--color-primary)';
                    yearButton.style.color = 'white';
                    yearButton.style.borderColor = 'var(--color-primary)';
                }
                
                yearButton.addEventListener('mouseenter', function() {
                    if (year !== currentYear) {
                        this.style.background = 'var(--color-primary-light)';
                        this.style.borderColor = 'var(--color-primary)';
                    }
                });
                
                yearButton.addEventListener('mouseleave', function() {
                    if (year !== currentYear) {
                        this.style.background = 'var(--bg-secondary)';
                        this.style.borderColor = 'var(--border)';
                    }
                });
                
                yearButton.addEventListener('click', function() {
                    periodoInput.value = year;
                    periodoPicker.style.display = 'none';
                    // Regenerar la grilla para actualizar el resaltado
                    generarGrillaAnos(currentDecade);
                    // Disparar evento change para que se actualice la búsqueda si es necesario
                    periodoInput.dispatchEvent(new Event('change', { bubbles: true }));
                });
                
                periodoYearGrid.appendChild(yearButton);
            }
        }
        
        // Mostrar/ocultar calendario al hacer clic en el icono
        periodoIcon.addEventListener('click', function(e) {
            e.stopPropagation();
            if (periodoPicker.style.display === 'none' || !periodoPicker.style.display) {
                currentDecade = Math.floor(parseInt(periodoInput.value || new Date().getFullYear()) / 10) * 10;
                generarGrillaAnos(currentDecade);
                periodoPicker.style.display = 'block';
            } else {
                periodoPicker.style.display = 'none';
            }
        });
        
        // Navegar a década anterior
        periodoYearPrev.addEventListener('click', function() {
            currentDecade -= 10;
            generarGrillaAnos(currentDecade);
        });
        
        // Navegar a década siguiente
        periodoYearNext.addEventListener('click', function() {
            currentDecade += 10;
            generarGrillaAnos(currentDecade);
        });
        
        // Cerrar calendario al hacer clic fuera
        document.addEventListener('click', function(e) {
            if (periodoPicker && !periodoPicker.contains(e.target) && e.target !== periodoIcon && e.target !== periodoInput) {
                periodoPicker.style.display = 'none';
            }
        });
        
        // Inicializar grilla con el año actual
        generarGrillaAnos(currentDecade);
    })();
    
    // ========== MODAL 1 (Ingreso de Calificaciones) ==========
    const modalOverlay1 = document.getElementById('ingreso-modal-overlay');
    const btnAbrirModal1 = document.getElementById('btn-abrir-modal');
    const btnCerrarModal1 = document.getElementById('btn-cerrar-modal');
    const btnCerrarModal1X = document.getElementById('btn-cerrar-modal-x');
    
    // Campos de input dentro del modal
    const modal1Ejercicio = document.getElementById('modal-ejercicio');
    const modal1Instrumento = document.getElementById('modal-instrumento');
    const modal1FechaPago = document.getElementById('modal-fecha_pago');
    const modal1Secuencia = document.getElementById('modal-secuencia');
    const modal1Mercado = document.getElementById('modal-mercado');
    const modal1MercadoSelect = document.getElementById('modal-mercado-select');
    const modal1Dividendo = document.getElementById('modal-dividendo');
    const modal1ISFUT = document.getElementById('modal-isfut');
    
    // Campos del dashboard
    const dashboardMercado = document.getElementById('mercado');
    const dashboardOrigen = document.getElementById('origen');
    const dashboardPeriodo = document.getElementById('periodo');

    // Botón "Ingresar" DENTRO del Modal 1
    const btnSiguienteModal = document.getElementById('btn-siguiente-modal'); 

    // Campos adicionales del modal
    const modal1Descripcion = document.getElementById('modal-descripcion');
    const modal1ValorHistorico = document.getElementById('modal-valor_historico');
    const modal1FactorActualizacion = document.getElementById('modal-factor_actualizacion');
    const modal1Anho = document.getElementById('modal-anho');

    // Obtener URLs desde window.DJANGO_URLS (configurado en el template)
    const ingresarUrl = window.DJANGO_URLS ? window.DJANGO_URLS.ingresar : '/ingresar/';

    // ============================================
    // FUNCIÓN: abrirModal1()
    // ============================================
    /**
     * Abre el modal de ingreso de calificaciones (Modal 1 - Datos básicos).
     * 
     * POR QUÉ ESTA FUNCIÓN ES NECESARIA:
     * - Es el primer paso del flujo de creación de calificaciones
     * - Prellena campos con valores del dashboard si es creación nueva
     * - No sobrescribe valores si es modificación (valores ya cargados)
     * - Maneja la lógica de mostrar select o input readonly según el contexto
     * 
     * CÓMO FUNCIONA:
     * 1. Verifica si es modificación o creación nueva
     * 2. Si es creación: copia valores del dashboard (mercado, período)
     * 3. Si es modificación: mantiene valores ya cargados (no sobrescribe)
     * 4. Muestra el modal cambiando display a 'flex'
     * 
     * FLUJO:
     * - Creación: Dashboard → Modal 1 (prellenado) → Modal 2 (factores)
     * - Modificación: Tabla → Modal 1 (datos cargados) → Modal 2 (factores)
     */
    function abrirModal1() { 
        // Verificar si estamos modificando una calificación existente
        // POR QUÉ: Necesitamos saber si es creación o modificación para manejar los valores correctamente
        // CÓMO: Buscamos un campo hidden que contiene el ID de la calificación
        // LÓGICA: Si existe y tiene valor, es modificación. Si no, es creación nueva
        const calificacionIdHidden = document.getElementById('calificacion-id-hidden');
        const esModificacion = calificacionIdHidden && calificacionIdHidden.value;
        
        // Si NO es modificación, copiar valores del dashboard (solo Mercado, no Año)
        // Si ES modificación, los valores ya fueron cargados y no debemos sobrescribirlos
        if (!esModificacion) {
            // Copia el valor actual Mercado del dashboard al campo del modal
            if (dashboardMercado) {
                const mercadoValue = dashboardMercado.value;
                const mercadoText = dashboardMercado.options[dashboardMercado.selectedIndex]?.text || mercadoValue || '';
                
                // Si el dashboard tiene "Todos" seleccionado (valor vacío), mostrar el select
                if (!mercadoValue || mercadoValue === '') {
                    // Mostrar select y ocultar input readonly
                    if (modal1Mercado) modal1Mercado.style.display = 'none';
                    if (modal1MercadoSelect) {
                        modal1MercadoSelect.style.display = 'block';
                        modal1MercadoSelect.value = ''; // Resetear a "Seleccione..."
                    }
                } else {
                    // Mostrar input readonly y ocultar select
                    if (modal1Mercado) {
                        modal1Mercado.style.display = 'block';
                        modal1Mercado.value = mercadoText;
                    }
                    if (modal1MercadoSelect) modal1MercadoSelect.style.display = 'none';
                }
            }
            // El campo Año ya no se copia del dashboard, el usuario lo elige manualmente
            // Establecer año máximo como el año actual
            if (modal1Anho) {
                const añoActual = new Date().getFullYear();
                modal1Anho.setAttribute('max', añoActual);
                // Si está vacío, establecer valor por defecto al año actual
                if (!modal1Anho.value) {
                    modal1Anho.value = añoActual;
                }
            }
        }
        // Si es modificación, los valores ya están cargados, no los sobrescribimos
        
        // Muestra el modal cambiando su estilo CSS
        if (modalOverlay1) modalOverlay1.style.display = 'flex'; 
    }
    
    /**
     * Cierra el modal de ingreso de calificaciones (Modal 1).
     * 
     * POR QUÉ ESTA FUNCIÓN ES NECESARIA:
     * - Permite cerrar el modal cuando el usuario cancela o termina
     * - Oculta el overlay y el contenido del modal
     * 
     * CÓMO FUNCIONA:
     * 1. Busca el elemento del overlay del modal
     * 2. Cambia su display a 'none' para ocultarlo
     */
    function cerrarModal1() { 
        // Ocultar el modal
        // POR QUÉ: El usuario quiere cerrar el modal
        // CÓMO: Cambiamos display a 'none' para ocultar el overlay
        // LÓGICA: Verificamos que el elemento exista antes de modificarlo
        if (modalOverlay1) modalOverlay1.style.display = 'none'; 
    }

    // Eventos (Listeners)
    if (btnAbrirModal1) {
        btnAbrirModal1.addEventListener('click', abrirModal1);
    }
    if (btnCerrarModal1) {
        btnCerrarModal1.addEventListener('click', cerrarModal1);
    }
    if (btnCerrarModal1X) {
        btnCerrarModal1X.addEventListener('click', cerrarModal1);
    }
    
    // Validar y sincronizar campo Año con Ejercicio
    if (modal1Anho) {
        // Establecer año máximo como el año actual
        const añoActual = new Date().getFullYear();
        modal1Anho.setAttribute('max', añoActual);
        
        // Sincronizar Ejercicio con Año cuando cambie el año
        modal1Anho.addEventListener('change', function() {
            const añoValor = parseInt(this.value);
            const añoActual = new Date().getFullYear();
            
            // Validar que no sea año futuro
            if (añoValor > añoActual) {
                mostrarNotificacion('No se pueden ingresar años futuros. Por favor, seleccione un año válido.', 'error');
                this.value = añoActual;
                this.style.borderColor = '#ff4444';
                setTimeout(() => {
                    this.style.borderColor = '';
                }, 3000);
            } else {
                this.style.borderColor = '';
            }
            
            // Sincronizar Ejercicio con Año
            if (modal1Ejercicio) {
                modal1Ejercicio.value = añoValor;
            }
        });
        
        // Validar también al escribir
        modal1Anho.addEventListener('input', function() {
            const añoValor = parseInt(this.value);
            const añoActual = new Date().getFullYear();
            
            if (this.value && !isNaN(añoValor)) {
                if (añoValor > añoActual) {
                    this.style.borderColor = '#ff4444';
                } else {
                    this.style.borderColor = '';
                    // Sincronizar Ejercicio con Año en tiempo real
                    if (modal1Ejercicio) {
                        modal1Ejercicio.value = añoValor;
                    }
                }
            }
        });
        
        // Validar al perder el foco
        modal1Anho.addEventListener('blur', function() {
            const añoValor = parseInt(this.value);
            const añoActual = new Date().getFullYear();
            
            if (this.value && !isNaN(añoValor)) {
                if (añoValor > añoActual) {
                    this.value = añoActual;
                    mostrarNotificacion('No se pueden ingresar años futuros. Se ha ajustado al año actual (' + añoActual + ').', 'warning');
                    this.style.borderColor = '#ffaa00';
                    setTimeout(() => {
                        this.style.borderColor = '';
                    }, 3000);
                    // Sincronizar Ejercicio
                    if (modal1Ejercicio) {
                        modal1Ejercicio.value = añoActual;
                    }
                } else {
                    // Sincronizar Ejercicio
                    if (modal1Ejercicio) {
                        modal1Ejercicio.value = añoValor;
                    }
                }
            }
        });
    }
    
    if (btnSiguienteModal) {
        btnSiguienteModal.addEventListener('click', function() {
            // Obtener el valor del mercado: del select si está visible, o del input readonly
            let mercadoValue = '';
            if (modal1MercadoSelect && modal1MercadoSelect.style.display !== 'none') {
                // Si el select está visible, usar su valor (puede ser modificación con dashboard en "Todos")
                mercadoValue = modal1MercadoSelect.value || '';
            } else if (modal1Mercado && modal1Mercado.style.display !== 'none') {
                // Si es readonly, verificar si es modificación o creación
                const calificacionIdHidden = document.getElementById('calificacion-id-hidden');
                const esModificacion = calificacionIdHidden && calificacionIdHidden.value;
                if (esModificacion) {
                    // En modificación, el readonly tiene el valor de la calificación
                    // Necesitamos obtener el valor real del mercado de la calificación
                    // Usar el valor del input readonly que ya tiene el mercado de la calificación
                    mercadoValue = modal1Mercado.value || '';
                } else {
                    // En creación, usar el valor del dashboard original
                    mercadoValue = dashboardMercado ? dashboardMercado.value || '' : '';
                }
            }
            
            // Validar campos mínimos requeridos
            if (!mercadoValue || mercadoValue.trim() === '') {
                mostrarMensaje('Campo Requerido', 'Debe seleccionar un Mercado', 'warning');
                return;
            }
            if (!modal1Instrumento || !modal1Instrumento.value.trim()) {
                mostrarMensaje('Campo Requerido', 'El campo Instrumento es obligatorio', 'warning');
                return;
            }
            if (!modal1Secuencia || !modal1Secuencia.value || parseInt(modal1Secuencia.value) <= 10000) {
                mostrarMensaje('Validación', 'La secuencia de evento debe ser mayor a 10,000', 'warning');
                return;
            }

            // Verificar si hay un ID de calificación (modificación) y datos guardados
            const calificacionIdHidden = document.getElementById('calificacion-id-hidden');
            const esModificacion = calificacionIdHidden && calificacionIdHidden.value;
            
            // Si es modificación y tenemos los datos guardados, abrir modal 2 directamente con los montos
            if (esModificacion && window.calificacionModificarData) {
                cerrarModal1();
                abrirModal2(window.calificacionModificarData);
                return;
            }
            
            // Preparar FormData con todos los campos
            const formData = new FormData();
            formData.append('Mercado', mercadoValue);
            // Obtener el origen del dashboard
            const origenValue = dashboardOrigen ? dashboardOrigen.value || '' : '';
            formData.append('Origen', origenValue);
            formData.append('Ejercicio', modal1Ejercicio ? modal1Ejercicio.value || modal1Anho.value : modal1Anho ? modal1Anho.value : '');
            formData.append('Instrumento', modal1Instrumento.value || '');
            formData.append('Descripcion', modal1Descripcion ? modal1Descripcion.value || '' : '');
            formData.append('FechaPago', modal1FechaPago ? modal1FechaPago.value || '' : '');
            formData.append('SecuenciaEvento', modal1Secuencia.value || '');
            formData.append('Dividendo', modal1Dividendo ? modal1Dividendo.value || '0.0' : '0.0');
            formData.append('ValorHistorico', modal1ValorHistorico ? modal1ValorHistorico.value || '0.0' : '0.0');
            formData.append('FactorActualizacion', modal1FactorActualizacion ? modal1FactorActualizacion.value || '0.0' : '0.0');
            formData.append('Anho', modal1Anho ? modal1Anho.value || '' : '');
            formData.append('ISFUT', modal1ISFUT && modal1ISFUT.checked ? 'true' : 'false');
            
            if (esModificacion) {
                formData.append('calificacion_id', calificacionIdHidden.value);
            }

            // Enviar datos via AJAX
            fetch(ingresarUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrftoken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    cerrarModal1();
                    abrirModal2(data);
                } else {
                    mostrarMensaje('Error', data.error || 'No se pudo crear la calificación', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                mostrarMensaje('Error', 'Error al enviar los datos. Por favor, intente nuevamente.', 'error');
            });
        });
    }

    // Evento para cerrar el modal si se hace clic en el fondo
    // Event listener para cerrar modal al hacer clic fuera eliminado por solicitud del usuario

    // ========== MODAL 2 (Factores - Montos) ==========
    const modalOverlay2 = document.getElementById('factores-modal-overlay');
    const btnCerrarModal2 = document.getElementById('btn-cerrar-modal-factores');
    const btnCerrarModal2X = document.getElementById('btn-cerrar-modal-factores-x');
    const btnGrabarFactores = document.getElementById('btn-grabar-factores');

    // Obtener URLs desde window.DJANGO_URLS (configurado en el template)
    const guardarFactoresUrl = window.DJANGO_URLS ? window.DJANGO_URLS.guardarFactores : '/guardar-factores/';
    const calcularFactoresUrl = window.DJANGO_URLS ? window.DJANGO_URLS.calcularFactores : '/calcular-factores/';

    // ============================================
    // FUNCIÓN: abrirModal2(data)
    // ============================================
    /**
     * Abre el modal de factores y montos (Modal 2 - Segundo paso).
     * 
     * POR QUÉ ESTA FUNCIÓN ES CRÍTICA:
     * - Es el segundo paso del flujo de creación de calificaciones
     * - Permite ingresar montos y calcular factores
     * - Muestra factores existentes si es modificación
     * - Prellena campos con datos de la calificación creada/modificada
     * 
     * CÓMO FUNCIONA:
     * 1. Recibe datos de la calificación (ID, datos básicos, factores, montos)
     * 2. Prellena todos los campos del modal con los datos recibidos
     * 3. Si es modificación: muestra factores originales como referencia
     * 4. Carga montos si están disponibles, o limpia campos si no
     * 5. Muestra el modal
     * 
     * FLUJO:
     * - Modal 1 guarda datos básicos → Retorna calificacion_id → Esta función abre Modal 2
     * - Usuario ingresa montos → Calcula factores → Guarda factores
     */
    function abrirModal2(data) {
        // Llenar campos del modal de factores con los datos recibidos
        const calificacionId = document.getElementById('calificacion_id');
        if (calificacionId) calificacionId.value = data.calificacion_id;
        
        const factoresMercado = document.getElementById('factores-mercado');
        if (factoresMercado) factoresMercado.value = data.data.mercado || '';
        
        const factoresInstrumento = document.getElementById('factores-instrumento');
        if (factoresInstrumento) factoresInstrumento.value = data.data.instrumento || '';
        
        const factoresEventoCapital = document.getElementById('factores-evento_capital');
        if (factoresEventoCapital) {
            // Si evento_capital está vacío, usar el valor de secuencia
            factoresEventoCapital.value = data.data.evento_capital || data.data.secuencia || '';
        }
        
        const factoresFechaPago = document.getElementById('factores-fecha_pago');
        if (factoresFechaPago) factoresFechaPago.value = data.data.fecha_pago || '';
        
        const factoresSecuencia = document.getElementById('factores-secuencia');
        if (factoresSecuencia) factoresSecuencia.value = data.data.secuencia || '';
        
        const factoresAnho = document.getElementById('factores-anho');
        if (factoresAnho) factoresAnho.value = data.data.anho || '';
        
        const factoresValorHistorico = document.getElementById('factores-valor_historico');
        if (factoresValorHistorico) factoresValorHistorico.value = data.data.valor_historico || '0.0';
        
        const factoresDescripcion = document.getElementById('factores-descripcion');
        if (factoresDescripcion) factoresDescripcion.value = data.data.descripcion || '';
        
        // Verificar si estamos modificando y mostrar factores originales como referencia
        const calificacionIdHidden = document.getElementById('calificacion-id-hidden');
        const esModificacion = calificacionIdHidden && calificacionIdHidden.value;
        
        // Si es modificación y tenemos factores guardados, mostrarlos como referencia
        if (esModificacion && data.factores && Object.keys(data.factores).length > 0) {
            const factoresSection = document.getElementById('factores-calculados-section');
            if (factoresSection) {
                factoresSection.style.display = 'block';
                // Cargar los factores originales en los campos de solo lectura como referencia
                for (const [fieldName, value] of Object.entries(data.factores)) {
                    const input = document.getElementById(fieldName);
                    if (input) {
                        const numValue = parseFloat(value);
                        if (!isNaN(numValue)) {
                            const formattedValue = numValue.toFixed(8).replace(/\.?0+$/, '');
                            input.value = formattedValue === '' ? '0' : formattedValue;
                        } else {
                            input.value = value || '0';
                        }
                    }
                }
            }
        } else {
            // Si NO es modificación, ocultar sección de factores calculados
            const factoresSection = document.getElementById('factores-calculados-section');
            if (factoresSection) factoresSection.style.display = 'none';
        }
        
        // Cargar montos si están disponibles en los datos, de lo contrario limpiar
        if (data.montos) {
            for (let i = 8; i <= 37; i++) {
                const montoField = `Monto${i.toString().padStart(2, '0')}`;
                const montoValue = data.montos[montoField] || '0.0';
                const montoInput = document.getElementById(`monto_${i}`);
                if (montoInput) {
                    // Formatear el valor a 2 decimales
                    const numValue = parseFloat(montoValue);
                    if (!isNaN(numValue)) {
                        montoInput.value = numValue.toFixed(2);
                    } else {
                        montoInput.value = '0.00';
                    }
                }
            }
        } else {
            // Limpiar todos los campos de montos si no hay datos
            for (let i = 8; i <= 37; i++) {
                const montoInput = document.getElementById(`monto_${i}`);
                if (montoInput) montoInput.value = '0.00';
            }
        }
        
        if (modalOverlay2) modalOverlay2.style.display = 'flex';
    }

    /**
     * Cierra el modal de factores y montos (Modal 2).
     * 
     * POR QUÉ ESTA FUNCIÓN ES NECESARIA:
     * - Permite cerrar el modal cuando el usuario cancela o termina
     * - Oculta el overlay y el contenido del modal
     * 
     * CÓMO FUNCIONA:
     * 1. Busca el elemento del overlay del modal
     * 2. Cambia su display a 'none' para ocultarlo
     */
    function cerrarModal2() {
        // Ocultar el modal
        // POR QUÉ: El usuario quiere cerrar el modal
        // CÓMO: Cambiamos display a 'none' para ocultar el overlay
        if (modalOverlay2) modalOverlay2.style.display = 'none';
    }

    if (btnCerrarModal2) {
        btnCerrarModal2.addEventListener('click', cerrarModal2);
    }
    if (btnCerrarModal2X) {
        btnCerrarModal2X.addEventListener('click', cerrarModal2);
    }

    // Event listener para cerrar modal al hacer clic fuera eliminado por solicitud del usuario

    // ============================================
    // FUNCIÓN: actualizarSumaBase()
    // ============================================
    /**
     * Calcula y actualiza la Suma Base en tiempo real mientras el usuario ingresa montos.
     * 
     * POR QUÉ ESTA FUNCIÓN ES IMPORTANTE:
     * - Muestra al usuario la Suma Base mientras escribe
     * - La Suma Base es crítica para calcular factores (Factor = Monto / SumaBase)
     * - Proporciona feedback inmediato sin necesidad de calcular factores
     * 
     * CÓMO FUNCIONA:
     * 1. Suma todos los montos del 8 al 19 (inclusive)
     * 2. Actualiza el campo de visualización de Suma Base
     * 3. Se ejecuta automáticamente cada vez que el usuario cambia un monto
     * 
     * FÓRMULA:
     * - SumaBase = suma de montos del 8 al 19
     * - Esta suma es el denominador para calcular todos los factores
     */
    function actualizarSumaBase() {
        let suma = 0;
        for (let i = 8; i <= 19; i++) {
            const input = document.getElementById(`monto_${i}`);
            if (input) {
                const valor = parseFloat(input.value) || 0;
                suma += valor;
            }
        }
        const sumaBaseDisplay = document.getElementById('suma-base-display');
        if (sumaBaseDisplay) {
            sumaBaseDisplay.value = suma.toFixed(2);
        }
    }

    // Agregar listeners a los campos de monto para calcular suma base en tiempo real
    for (let i = 8; i <= 19; i++) {
        const input = document.getElementById(`monto_${i}`);
        if (input) {
            input.addEventListener('input', actualizarSumaBase);
        }
    }

    // Botón Calcular
    const btnCalcularFactores = document.getElementById('btn-calcular-factores');
    if (btnCalcularFactores) {
        btnCalcularFactores.addEventListener('click', function() {
            const formFactores = document.getElementById('form-factores');
            if (!formFactores) {
                mostrarMensaje('Error', 'No se encontró el formulario de factores', 'error');
                return;
            }

            const calificacionId = document.getElementById('calificacion_id');
            if (!calificacionId || !calificacionId.value) {
                mostrarMensaje('Error', 'No se encontró el ID de la calificación', 'error');
                return;
            }

            // Enviar todos los valores del formulario para calcular (MONTOS)
            const formData = new FormData(formFactores);

            fetch(calcularFactoresUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrftoken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Mostrar información de debug en la consola
                    if (data.debug) {
                        console.log('=== Información de Cálculo ===');
                        console.log('Suma Base:', data.debug.suma_base);
                        console.log('==============================');
                    }
                    
                    // Actualizar el campo de suma base
                    const sumaBaseDisplay = document.getElementById('suma-base-display');
                    if (sumaBaseDisplay && data.suma_base) {
                        sumaBaseDisplay.value = parseFloat(data.suma_base).toFixed(2);
                    }
                    
                    // Actualizar los campos de factores calculados con los valores calculados
                    if (data.factores) {
                        let actualizados = 0;
                        for (const [fieldName, value] of Object.entries(data.factores)) {
                            const input = document.getElementById(fieldName);
                            if (input) {
                                // Convertir el valor a número y formatearlo correctamente
                                const numValue = parseFloat(value);
                                if (!isNaN(numValue)) {
                                    // Formatear con hasta 8 decimales
                                    const formattedValue = numValue.toFixed(8).replace(/\.?0+$/, '');
                                    input.value = formattedValue === '' ? '0' : formattedValue;
                                    actualizados++;
                                } else {
                                    input.value = value || '0';
                                    actualizados++;
                                }
                            }
                        }
                        console.log(`Total de factores actualizados: ${actualizados}`);
                    }
                    
                    // Mostrar la sección de factores calculados
                    const factoresSection = document.getElementById('factores-calculados-section');
                    if (factoresSection) {
                        factoresSection.style.display = 'block';
                        factoresSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }
                    
                    mostrarMensaje('Éxito', 'Factores calculados exitosamente. Los valores han sido actualizados en el formulario.', 'success');
                } else {
                    mostrarMensaje('Error', data.error || 'No se pudieron calcular los factores', 'error');
                    console.error('Error en cálculo:', data);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                mostrarMensaje('Error', 'Error al calcular. Por favor, intente nuevamente.', 'error');
            });
        });
    }

    // Botón Grabar
    if (btnGrabarFactores) {
        btnGrabarFactores.addEventListener('click', function() {
            const formFactores = document.getElementById('form-factores');
            if (!formFactores) {
                mostrarMensaje('Error', 'No se encontró el formulario de factores', 'error');
                return;
            }
            
            const formData = new FormData(formFactores);
            
            fetch(guardarFactoresUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrftoken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    mostrarMensaje('Éxito', 'Factores guardados exitosamente', 'success');
                    cerrarModal2();
                    // Recargar la página para ver los cambios después de cerrar el modal
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    mostrarMensaje('Error', data.error || 'No se pudieron guardar los factores', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                mostrarMensaje('Error', 'Error al guardar. Por favor, intente nuevamente.', 'error');
            });
        });
    }

    // ========== BOTÓN BUSCAR ==========
    const btnBuscar = document.getElementById('btn-buscar');
    const btnLimpiar = document.getElementById('btn-limpiar');
    const btnExportar = document.getElementById('btn-exportar');
    const buscarCalificacionesUrl = window.DJANGO_URLS ? window.DJANGO_URLS.buscarCalificaciones : '/buscar-calificaciones/';
    const tablaBody = document.getElementById('tabla-calificaciones-body');

    // ============================================
    // FUNCIÓN: formatearNumero(valor)
    // ============================================
    /**
     * Formatea un número eliminando ceros innecesarios y manteniendo precisión.
     * 
     * POR QUÉ ESTA FUNCIÓN ES ÚTIL:
     * - Mejora la presentación de números en la interfaz
     * - Elimina ceros innecesarios (ej: "0.25000000" → "0.25")
     * - Mantiene precisión de hasta 8 decimales cuando es necesario
     * - Convierte valores inválidos a "0"
     * 
     * CÓMO FUNCIONA:
     * 1. Valida que el valor no sea null, undefined, o "0"
     * 2. Convierte a número usando parseFloat
     * 3. Si es NaN, retorna "0"
     * 4. Formatea con hasta 8 decimales
     * 5. Elimina ceros innecesarios al final
     * 
     * Parámetros:
     *   - valor: Valor a formatear (string o number)
     * 
     * Retorna:
     *   - string: Número formateado sin ceros innecesarios
     */
    function formatearNumero(valor) {
        // Validar que el valor no sea null, undefined, o "0"
        // POR QUÉ: Estos valores deben mostrarse como "0" en la interfaz
        // CÓMO: Verificamos múltiples variaciones de cero
        // LÓGICA: Si el valor es alguno de estos, retornamos "0" directamente
        if (!valor || valor === '0' || valor === '0.0' || valor === '0.00000000') {
            return '0';
        }
        
        // Convertir el valor a número
        // POR QUÉ: Necesitamos un número para formatearlo correctamente
        // CÓMO: parseFloat() convierte string a número decimal
        // LÓGICA: Si el valor es "123.45", parseFloat() retorna 123.45
        const num = parseFloat(valor);
        
        // Validar que sea un número válido
        // POR QUÉ: Si parseFloat() no puede convertir, retorna NaN
        // CÓMO: isNaN() verifica si el valor es "Not a Number"
        // LÓGICA: Si es NaN, retornamos "0" como valor por defecto
        if (isNaN(num)) return '0';
        
        // Formatear con hasta 8 decimales, eliminando ceros innecesarios
        return num.toFixed(8).replace(/\.?0+$/, '');
    }

    // ============================================
    // FUNCIÓN: renderizarCalificaciones(calificaciones)
    // ============================================
    /**
     * Renderiza las calificaciones en la tabla del dashboard.
     * 
     * POR QUÉ ESTA FUNCIÓN ES CRÍTICA:
     * - Actualiza la tabla dinámicamente sin recargar la página
     * - Muestra todas las calificaciones con sus factores
     * - Agrega botones de acción (modificar, eliminar, copiar, ver logs)
     * - Formatea números para mejor presentación
     * 
     * CÓMO FUNCIONA:
     * 1. Valida que exista el elemento tablaBody
     * 2. Si no hay calificaciones, muestra mensaje de "no encontradas"
     * 3. Si hay calificaciones, genera HTML para cada fila
     * 4. Incluye botones de acción con data-attributes para identificar cada calificación
     * 5. Formatea factores usando formatearNumero()
     * 6. Inserta el HTML en la tabla
     * 7. Agrega event listeners a los botones
     * 
     * Parámetros:
     *   - calificaciones: Array de objetos con datos de calificaciones
     * 
     * Retorna: void
     */
    function renderizarCalificaciones(calificaciones) {
        // Validar que el elemento tablaBody exista
        // POR QUÉ: No podemos renderizar si no existe el contenedor
        // CÓMO: Si no existe, salimos de la función inmediatamente
        if (!tablaBody) return;

        // Verificar si hay calificaciones para mostrar
        // POR QUÉ: Si no hay calificaciones, mostramos un mensaje informativo
        // CÓMO: Verificamos si el array está vacío o es null/undefined
        // LÓGICA: Si no hay calificaciones, mostramos mensaje y salimos
        if (!calificaciones || calificaciones.length === 0) {
            tablaBody.innerHTML = `
                <tr>
                    <td colspan="38" style="text-align: center; padding: 20px;">
                        <em>No se encontraron calificaciones con los filtros seleccionados</em>
                    </td>
                </tr>
            `;
            return;
        }

        let html = '';
        calificaciones.forEach(cal => {
            // Asegurar que el ID esté disponible
            const calId = cal.id || cal._id || '';
            if (!calId) {
                console.warn('Calificación sin ID:', cal);
            }
            
            html += '<tr>';
            
            // Columna de Acciones con botones con iconos Bootstrap Icons
            html += `<td class="acciones-cell">
                <button class="btn-row-icon btn-modificar-row" data-calificacion-id="${calId}" title="Modificar">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn-row-icon btn-eliminar-row" data-calificacion-id="${calId}" title="Eliminar">
                    <i class="bi bi-trash"></i>
                </button>
                <button class="btn-row-icon btn-copiar-row" data-calificacion-id="${calId}" title="Copiar">
                    <i class="bi bi-copy"></i>
                </button>
                <button class="btn-row-icon btn-log-row" data-calificacion-id="${calId}" title="Ver Log de Cambios">
                    <i class="bi bi-file-text"></i>
                </button>
            </td>`;
            
            // Columnas básicas
            html += `<td>${cal.ejercicio || ''}</td>`;
            html += `<td>${cal.instrumento || ''}</td>`;
            html += `<td>${cal.fecha_pago || ''}</td>`;
            html += `<td>${cal.descripcion || ''}</td>`;
            html += `<td>${cal.secuencia_evento || ''}</td>`;
            html += `<td>${cal.fecha_act || ''}</td>`;
            
            // Factores 8-37
            for (let i = 8; i < 38; i++) {
                const factorName = `Factor${i.toString().padStart(2, '0')}`;
                const valor = cal.factores && cal.factores[factorName] ? cal.factores[factorName] : '0.0';
                html += `<td>${formatearNumero(valor)}</td>`;
            }
            
            html += '</tr>';
        });

        tablaBody.innerHTML = html;
        
        // Agregar event listeners a los botones después de renderizar
        agregarEventListenersBotones();
    }

    if (btnBuscar) {
        btnBuscar.addEventListener('click', function() {
            const mercado = dashboardMercado ? dashboardMercado.value : '';
            const origen = dashboardOrigen ? dashboardOrigen.value : '';
            const periodo = dashboardPeriodo ? dashboardPeriodo.value : '';

            // Construir URL con parámetros
            const params = new URLSearchParams();
            if (mercado) params.append('mercado', mercado);
            if (origen) params.append('origen', origen);
            if (periodo) params.append('periodo', periodo);

            const url = `${buscarCalificacionesUrl}?${params.toString()}`;

            // Mostrar mensaje de carga
            if (tablaBody) {
                tablaBody.innerHTML = `
                    <tr>
                        <td colspan="38" style="text-align: center; padding: 20px;">
                            <em>Buscando calificaciones...</em>
                        </td>
                    </tr>
                `;
            }

            fetch(url, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': csrftoken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderizarCalificaciones(data.calificaciones);
                    console.log(`Se encontraron ${data.total} calificación(es)`);
                } else {
                    mostrarMensaje('Error', data.error || 'No se pudieron buscar las calificaciones', 'error');
                    if (tablaBody) {
                        tablaBody.innerHTML = `
                            <tr>
                                <td colspan="38" style="text-align: center; padding: 20px; color: red;">
                                    <em>Error al buscar calificaciones</em>
                                </td>
                            </tr>
                        `;
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                mostrarMensaje('Error', 'Error al buscar. Por favor, intente nuevamente.', 'error');
                if (tablaBody) {
                    tablaBody.innerHTML = `
                        <tr>
                            <td colspan="38" style="text-align: center; padding: 20px; color: red;">
                                <em>Error al buscar calificaciones</em>
                            </td>
                        </tr>
                    `;
                }
            });
        });
    }

    // ============================================
    // FUNCIÓN: agregarEventListenersBotones()
    // ============================================
    /**
     * Agrega event listeners a todos los botones de acción de las filas de calificaciones.
     * 
     * POR QUÉ ESTA FUNCIÓN ES NECESARIA:
     * - Los botones se crean dinámicamente al renderizar la tabla
     * - Necesitan event listeners para funcionar (modificar, eliminar, copiar, ver logs)
     * - Se llama después de cada renderizado para asegurar que los botones funcionen
     * 
     * CÓMO FUNCIONA:
     * 1. Busca todos los botones de cada tipo (modificar, eliminar, copiar, log)
     * 2. Para cada botón, obtiene el ID de la calificación desde data-attribute
     * 3. Agrega event listener que llama a la función correspondiente
     * 4. Valida que el ID exista antes de ejecutar la acción
     * 
     * Botones configurados:
     * - .btn-modificar-row: Llama a modificarCalificacion()
     * - .btn-eliminar-row: Llama a eliminarCalificacion()
     * - .btn-copiar-row: Llama a copiarCalificacion()
     * - .btn-log-row: Llama a verLogCalificacion()
     */
    function agregarEventListenersBotones() {
        // Botones MODIFICAR
        const botonesModificar = document.querySelectorAll('.btn-modificar-row');
        console.log('Botones modificar encontrados:', botonesModificar.length);
        botonesModificar.forEach((btn, index) => {
            const calId = btn.getAttribute('data-calificacion-id');
            console.log(`Botón modificar ${index}: ID =`, calId);
            btn.addEventListener('click', function() {
                const calificacionId = this.getAttribute('data-calificacion-id');
                console.log('Botón modificar clickeado, ID obtenido:', calificacionId);
                if (calificacionId && calificacionId.trim() !== '') {
                    modificarCalificacion(calificacionId);
                } else {
                    console.error('ID de calificación vacío o no encontrado');
                    mostrarMensaje('Error', 'No se encontró el ID de la calificación', 'error');
                }
            });
        });

        // Botones ELIMINAR
        const botonesEliminar = document.querySelectorAll('.btn-eliminar-row');
        console.log('Botones eliminar encontrados:', botonesEliminar.length);
        botonesEliminar.forEach((btn, index) => {
            const calId = btn.getAttribute('data-calificacion-id');
            console.log(`Botón eliminar ${index}: ID =`, calId);
            btn.addEventListener('click', function() {
                const calificacionId = this.getAttribute('data-calificacion-id');
                console.log('Botón eliminar clickeado, ID obtenido:', calificacionId);
                if (calificacionId && calificacionId.trim() !== '') {
                    eliminarCalificacion(calificacionId);
                } else {
                    console.error('ID de calificación vacío o no encontrado');
                    mostrarMensaje('Error', 'No se encontró el ID de la calificación', 'error');
                }
            });
        });

        // Botones COPIAR
        const botonesCopiar = document.querySelectorAll('.btn-copiar-row');
        console.log('Botones copiar encontrados:', botonesCopiar.length);
        botonesCopiar.forEach((btn, index) => {
            const calId = btn.getAttribute('data-calificacion-id');
            console.log(`Botón copiar ${index}: ID =`, calId);
            btn.addEventListener('click', function() {
                const calificacionId = this.getAttribute('data-calificacion-id');
                console.log('Botón copiar clickeado, ID obtenido:', calificacionId);
                if (calificacionId && calificacionId.trim() !== '') {
                    copiarCalificacion(calificacionId);
                } else {
                    console.error('ID de calificación vacío o no encontrado');
                    mostrarMensaje('Error', 'No se encontró el ID de la calificación', 'error');
                }
            });
        });

        // Botones LOG
        const botonesLog = document.querySelectorAll('.btn-log-row');
        console.log('Botones log encontrados:', botonesLog.length);
        botonesLog.forEach((btn, index) => {
            const calId = btn.getAttribute('data-calificacion-id');
            console.log(`Botón log ${index}: ID =`, calId);
            btn.addEventListener('click', function() {
                const calificacionId = this.getAttribute('data-calificacion-id');
                console.log('Botón log clickeado, ID obtenido:', calificacionId);
                if (calificacionId && calificacionId.trim() !== '') {
                    verLogCalificacion(calificacionId);
                } else {
                    console.error('ID de calificación vacío o no encontrado');
                    mostrarMensaje('Error', 'No se encontró el ID de la calificación', 'error');
                }
            });
        });
    }

    // ============================================
    // FUNCIÓN: modificarCalificacion(calificacionId)
    // ============================================
    /**
     * Obtiene los datos de una calificación y abre el modal de edición.
     * 
     * POR QUÉ ESTA FUNCIÓN ES IMPORTANTE:
     * - Permite editar calificaciones existentes
     * - Carga datos desde el servidor para prellenar formularios
     * - Calcula montos desde factores guardados (cálculo inverso)
     * - Maneja el flujo completo de modificación
     * 
     * CÓMO FUNCIONA:
     * 1. Valida que el ID no esté vacío
     * 2. Envía petición AJAX al servidor para obtener datos de la calificación
     * 3. El servidor calcula montos desde factores (Monto = Factor * SumaBase)
     * 4. Prellena Modal 1 con datos básicos
     * 5. Guarda datos en window.calificacionModificarData para Modal 2
     * 6. Abre Modal 1 para editar
     * 
     * CÁLCULO INVERSO:
     * - Si tenemos factores y SumaBase, podemos calcular montos
     * - Fórmula: Monto = Factor * SumaBase
     * - Esto permite reconstruir montos cuando solo tenemos factores guardados
     * 
     * Parámetros:
     *   - calificacionId: ID de la calificación a modificar
     */
    function modificarCalificacion(calificacionId) {
        // Validar que el ID no esté vacío
        if (!calificacionId || calificacionId.trim() === '') {
            mostrarMensaje('Error', 'No se encontró el ID de la calificación', 'error');
            return;
        }
        
        // Obtener datos de la calificación desde el backend
        let obtenerCalificacionUrl;
        if (window.DJANGO_URLS && window.DJANGO_URLS.obtenerCalificacionBase) {
            // Reemplazar el ID placeholder con el ID real
            obtenerCalificacionUrl = window.DJANGO_URLS.obtenerCalificacionBase.replace('000000000000000000000000', calificacionId);
        } else {
            obtenerCalificacionUrl = `/prueba/obtener-calificacion/${calificacionId}/`;
        }
        
        // Asegurar que la URL no tenga doble barra
        obtenerCalificacionUrl = obtenerCalificacionUrl.replace(/\/+/g, '/').replace(':/', '://');
        console.log('Obteniendo calificación con URL:', obtenerCalificacionUrl, 'ID:', calificacionId);
        fetch(obtenerCalificacionUrl, {
            method: 'GET',
            headers: {
                'X-CSRFToken': csrftoken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Cargar datos en el modal de ingreso
                const cal = data.calificacion;
                
                // Llenar campos del modal 1
                // Para modificar: mostrar select si el dashboard tiene "Todos", sino mostrar readonly
                const mercadoValue = dashboardMercado ? dashboardMercado.value : '';
                if (!mercadoValue || mercadoValue === '') {
                    // Dashboard tiene "Todos" seleccionado: mostrar select para permitir cambiar
                    if (modal1Mercado) modal1Mercado.style.display = 'none';
                    if (modal1MercadoSelect) {
                        modal1MercadoSelect.style.display = 'block';
                        modal1MercadoSelect.value = cal.mercado || '';
                    }
                } else {
                    // Dashboard tiene un mercado específico: mostrar readonly
                    if (modal1Mercado) {
                        modal1Mercado.value = cal.mercado || '';
                        modal1Mercado.style.display = 'block';
                    }
                    if (modal1MercadoSelect) modal1MercadoSelect.style.display = 'none';
                }
                if (modal1Instrumento) modal1Instrumento.value = cal.instrumento || '';
                if (modal1Descripcion) modal1Descripcion.value = cal.descripcion || '';
                if (modal1FechaPago) {
                    if (cal.fecha_pago) {
                        const fecha = new Date(cal.fecha_pago);
                        modal1FechaPago.value = fecha.toISOString().split('T')[0];
                    }
                }
                if (modal1Secuencia) modal1Secuencia.value = cal.secuencia_evento || '';
                if (modal1Dividendo) modal1Dividendo.value = cal.dividendo || '0.0';
                if (modal1ISFUT) modal1ISFUT.checked = cal.isfut || false;
                if (modal1Ejercicio) modal1Ejercicio.value = cal.ejercicio || '';
                if (modal1Anho) modal1Anho.value = cal.anho || '';
                if (modal1ValorHistorico) modal1ValorHistorico.value = cal.valor_historico || '0.0';
                if (modal1FactorActualizacion) modal1FactorActualizacion.value = cal.factor_actualizacion || '0.0';
                
                // Guardar el ID de la calificación para actualizar
                const formIngreso = document.getElementById('form-ingreso');
                if (!document.getElementById('calificacion-id-hidden')) {
                    const hiddenInput = document.createElement('input');
                    hiddenInput.type = 'hidden';
                    hiddenInput.id = 'calificacion-id-hidden';
                    hiddenInput.name = 'calificacion_id';
                    if (formIngreso) formIngreso.appendChild(hiddenInput);
                }
                document.getElementById('calificacion-id-hidden').value = calificacionId;
                
                // Guardar los datos de la calificación (incluyendo montos y factores) para usar al abrir modal 2
                window.calificacionModificarData = {
                    calificacion_id: calificacionId,
                    data: {
                        mercado: cal.mercado || '',
                        instrumento: cal.instrumento || '',
                        fecha_pago: cal.fecha_pago || '',
                        secuencia: cal.secuencia_evento || '',
                        anho: cal.anho || '',
                        valor_historico: cal.valor_historico || '0.0',
                        descripcion: cal.descripcion || ''
                    },
                    montos: cal.montos || {},
                    factores: cal.factores || {}
                };
                
                // Abrir modal 1 con los datos cargados (flujo normal, no abrir modal 2 todavía)
                abrirModal1();
            } else {
                mostrarMensaje('Error', data.error || 'No se pudo cargar la calificación', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarMensaje('Error', 'Error al cargar la calificación. Por favor, intente nuevamente.', 'error');
        });
    }

    // ============================================
    // FUNCIÓN: eliminarCalificacion(calificacionId)
    // ============================================
    /**
     * Elimina una calificación después de confirmación del usuario.
     * 
     * POR QUÉ ESTA FUNCIÓN ES IMPORTANTE:
     * - Permite eliminar calificaciones del sistema
     * - Muestra confirmación antes de eliminar (previene eliminaciones accidentales)
     * - Actualiza la tabla después de eliminar sin recargar la página
     * - Maneja errores y muestra mensajes apropiados
     * 
     * CÓMO FUNCIONA:
     * 1. Valida que el ID no esté vacío
     * 2. Muestra modal de confirmación
     * 3. Si el usuario confirma, envía petición AJAX al servidor
     * 4. El servidor elimina la calificación de MongoDB
     * 5. Actualiza la tabla mostrando todas las calificaciones
     * 
     * Parámetros:
     *   - calificacionId: ID de la calificación a eliminar
     */
    function eliminarCalificacion(calificacionId) {
        // Validar que el ID no esté vacío
        if (!calificacionId || calificacionId.trim() === '') {
            mostrarMensaje('Error', 'No se encontró el ID de la calificación', 'error');
            return;
        }
        
        mostrarConfirmacion(
            'Confirmar Eliminación',
            '¿Estás seguro de que deseas eliminar esta calificación?',
            'Esta acción no se puede deshacer.',
            function() {
                let eliminarCalificacionUrl;
                if (window.DJANGO_URLS && window.DJANGO_URLS.eliminarCalificacionBase) {
                    // Reemplazar el ID placeholder con el ID real
                    eliminarCalificacionUrl = window.DJANGO_URLS.eliminarCalificacionBase.replace('000000000000000000000000', calificacionId);
                } else {
                    eliminarCalificacionUrl = `/prueba/eliminar-calificacion/${calificacionId}/`;
                }
                
                // Asegurar que la URL no tenga doble barra
                eliminarCalificacionUrl = eliminarCalificacionUrl.replace(/\/+/g, '/').replace(':/', '://');
                console.log('Eliminando calificación con URL:', eliminarCalificacionUrl, 'ID:', calificacionId);
                fetch(eliminarCalificacionUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrftoken
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        mostrarMensaje('Éxito', 'Calificación eliminada exitosamente.', 'success');
                        // Resetear filtros para mostrar todas las calificaciones
                        if (dashboardMercado) dashboardMercado.value = '';
                        if (dashboardOrigen) dashboardOrigen.value = '';
                        if (dashboardPeriodo) dashboardPeriodo.value = '';
                        // Recargar la tabla con todas las calificaciones
                        if (btnBuscar) btnBuscar.click();
                    } else {
                        mostrarMensaje('Error', data.error || 'No se pudo eliminar la calificación', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    mostrarMensaje('Error', 'Error al eliminar. Por favor, intente nuevamente.', 'error');
                });
            },
            'danger'
        );
    }

    // ============================================
    // FUNCIÓN: copiarCalificacion(calificacionId)
    // ============================================
    /**
     * Copia una calificación completa creando una nueva con todos los datos.
     * 
     * POR QUÉ ESTA FUNCIÓN ES ÚTIL:
     * - Permite duplicar calificaciones existentes
     * - Útil para crear variaciones de una calificación base
     * - Copia todos los campos: datos básicos, factores, montos, SumaBase
     * - La nueva calificación tiene un ID único (nuevo documento en MongoDB)
     * 
     * CÓMO FUNCIONA:
     * 1. Valida que el ID no esté vacío
     * 2. Muestra confirmación antes de copiar
     * 3. Si el usuario confirma, envía petición AJAX al servidor
     * 4. El servidor crea una copia completa con nuevo ID
     * 5. Actualiza la tabla para mostrar la nueva calificación
     * 
     * Parámetros:
     *   - calificacionId: ID de la calificación a copiar
     */
    function copiarCalificacion(calificacionId) {
        // Validar que el ID no esté vacío
        if (!calificacionId || calificacionId.trim() === '') {
            mostrarMensaje('Error', 'No se encontró el ID de la calificación', 'error');
            return;
        }
        
        // Mostrar confirmación antes de copiar
        mostrarConfirmacion(
            'Copiar Calificación',
            '¿Está seguro de que desea copiar esta calificación? Se creará una nueva calificación con todos los datos copiados.',
            null, // advertencia (opcional)
            function() {
                // Obtener URL para copiar calificación
                let copiarCalificacionUrl;
                if (window.DJANGO_URLS && window.DJANGO_URLS.copiarCalificacionBase) {
                    copiarCalificacionUrl = window.DJANGO_URLS.copiarCalificacionBase.replace('000000000000000000000000', calificacionId);
                } else {
                    copiarCalificacionUrl = `/prueba/copiar-calificacion/${calificacionId}/`;
                }
                
                copiarCalificacionUrl = copiarCalificacionUrl.replace(/\/+/g, '/').replace(':/', '://');
                console.log('Copiando calificación con URL:', copiarCalificacionUrl, 'ID:', calificacionId);
                
                fetch(copiarCalificacionUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrftoken,
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => {
                    console.log('Respuesta del servidor:', response.status, response.statusText);
                    if (!response.ok) {
                        return response.text().then(text => {
                            console.error('Error del servidor:', text);
                            throw new Error(`Error del servidor: ${response.status} ${response.statusText}`);
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Datos recibidos:', data);
                    if (data.success) {
                        mostrarMensaje('Éxito', 'Calificación copiada exitosamente', 'success');
                        // Recargar la página para mostrar la nueva calificación
                        setTimeout(() => {
                            window.location.reload();
                        }, 1500);
                    } else {
                        mostrarMensaje('Error', data.error || 'No se pudo copiar la calificación', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error completo:', error);
                    mostrarMensaje('Error', 'Error al copiar la calificación: ' + error.message, 'error');
                });
            },
            'primary', // tipoBotonConfirmar (no 'danger' para que no sea rojo)
            'Copiar' // textoBotonConfirmar
        );
    }

    // ========== MODAL DE LOGS DE CALIFICACIÓN ==========
    const modalLogCalificacionOverlay = document.getElementById('log-calificacion-modal-overlay');
    const btnCerrarLogCalificacion = document.getElementById('btn-cerrar-log-calificacion');
    const btnCerrarLogCalificacionX = document.getElementById('btn-cerrar-log-calificacion-x');

    /**
     * Cierra el modal de logs de calificación.
     * 
     * POR QUÉ ESTA FUNCIÓN ES NECESARIA:
     * - Permite cerrar el modal cuando el usuario termina de revisar los logs
     * - Oculta el overlay y el contenido del modal
     * 
     * CÓMO FUNCIONA:
     * 1. Busca el elemento del overlay del modal
     * 2. Cambia su display a 'none' para ocultarlo
     */
    function cerrarModalLogCalificacion() {
        // Ocultar el modal
        // POR QUÉ: El usuario quiere cerrar el modal
        // CÓMO: Cambiamos display a 'none' para ocultar el overlay
        if (modalLogCalificacionOverlay) modalLogCalificacionOverlay.style.display = 'none';
    }

    if (btnCerrarLogCalificacion) {
        btnCerrarLogCalificacion.addEventListener('click', cerrarModalLogCalificacion);
    }
    if (btnCerrarLogCalificacionX) {
        btnCerrarLogCalificacionX.addEventListener('click', cerrarModalLogCalificacion);
    }

    // ========== FUNCIÓN PARA VER LOG DE CALIFICACIÓN ==========
    // ============================================
    // FUNCIÓN: verLogCalificacion(calificacionId)
    // ============================================
    /**
     * Obtiene y muestra los logs de auditoría de una calificación específica.
     * 
     * POR QUÉ ESTA FUNCIÓN ES ÚTIL:
     * - Permite ver el historial completo de cambios de una calificación
     * - Muestra quién hizo qué cambios y cuándo
     * - Útil para auditoría y debugging
     * - Muestra cambios detallados en formato legible
     * 
     * CÓMO FUNCIONA:
     * 1. Valida que el ID no esté vacío
     * 2. Envía petición AJAX al servidor para obtener logs
     * 3. El servidor busca todos los logs relacionados con esa calificación
     * 4. Retorna logs con información del actor y cambios detallados
     * 5. Llama a mostrarLogsCalificacion() para mostrar en modal
     * 
     * Parámetros:
     *   - calificacionId: ID de la calificación para obtener sus logs
     */
    function verLogCalificacion(calificacionId) {
        // Validar que el ID no esté vacío
        if (!calificacionId || calificacionId.trim() === '') {
            mostrarMensaje('Error', 'No se encontró el ID de la calificación', 'error');
            return;
        }
        
        // Obtener URL para obtener logs
        let obtenerLogsUrl;
        if (window.DJANGO_URLS && window.DJANGO_URLS.obtenerLogsCalificacionBase) {
            obtenerLogsUrl = window.DJANGO_URLS.obtenerLogsCalificacionBase.replace('000000000000000000000000', calificacionId);
        } else {
            obtenerLogsUrl = `/prueba/obtener-logs-calificacion/${calificacionId}/`;
        }
        
        obtenerLogsUrl = obtenerLogsUrl.replace(/\/+/g, '/').replace(':/', '://');
        console.log('Obteniendo logs con URL:', obtenerLogsUrl, 'ID:', calificacionId);
        
        fetch(obtenerLogsUrl, {
            method: 'GET',
            headers: {
                'X-CSRFToken': csrftoken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                mostrarLogsCalificacion(data.logs, data.calificacion_info);
            } else {
                mostrarMensaje('Error', data.error || 'No se pudieron cargar los logs', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarMensaje('Error', 'Error al cargar los logs. Por favor, intente nuevamente.', 'error');
        });
    }

    // Variables globales para almacenar datos de logs (para regenerar cuando cambie el tema)
    let logsCalificacionActuales = null;
    let calificacionInfoActual = null;

    // ============================================
    // FUNCIÓN: mostrarLogsCalificacion(logs, calificacionInfo)
    // ============================================
    /**
     * Muestra los logs de auditoría de una calificación en un modal.
     * 
     * POR QUÉ ESTA FUNCIÓN ES IMPORTANTE:
     * - Presenta los logs de forma legible y organizada
     * - Separa cambios por tipo (factores, montos, campos básicos)
     * - Muestra valores anteriores y nuevos de forma clara
     * - Adapta colores según el tema (oscuro/claro)
     * - Permite ver el historial completo de una calificación
     * 
     * CÓMO FUNCIONA:
     * 1. Recibe logs y información de la calificación
     * 2. Guarda datos para regenerar cuando cambie el tema
     * 3. Llena información básica de la calificación
     * 4. Para cada log:
     *    a. Formatea fecha y acción
     *    b. Separa cambios por tipo (factores, montos, básicos)
     *    c. Genera HTML con colores según tema
     *    d. Muestra valores anteriores y nuevos
     * 5. Inserta HTML en la tabla del modal
     * 6. Muestra el modal
     * 
     * Parámetros:
     *   - logs: Array de objetos con información de cada log
     *   - calificacionInfo: Objeto con información básica de la calificación
     */
    function mostrarLogsCalificacion(logs, calificacionInfo) {
        const modalOverlay = document.getElementById('log-calificacion-modal-overlay');
        if (!modalOverlay) {
            mostrarMensaje('Error', 'No se encontró el modal de logs', 'error');
            return;
        }

        // Guardar datos actuales para poder regenerar cuando cambie el tema
        logsCalificacionActuales = logs;
        calificacionInfoActual = calificacionInfo;

        // Llenar información de la calificación
        const infoCalificacion = document.getElementById('log-calificacion-info');
        if (infoCalificacion && calificacionInfo) {
            infoCalificacion.innerHTML = `
                <strong>Ejercicio:</strong> ${calificacionInfo.ejercicio || 'N/A'}<br>
                <strong>Instrumento:</strong> ${calificacionInfo.instrumento || 'N/A'}<br>
                <strong>Mercado:</strong> ${calificacionInfo.mercado || 'N/A'}
            `;
        }

        // Función auxiliar para detectar el tema oscuro dinámicamente
        function detectarTemaOscuro() {
            return document.body.classList.contains('dark-theme') || document.documentElement.classList.contains('dark-theme');
        }
        
        // Llenar tabla de logs
        const tbody = document.getElementById('log-calificacion-tbody');
        if (tbody) {
            if (logs && logs.length > 0) {
                let html = '';
                logs.forEach(log => {
                    // Detectar tema oscuro dinámicamente para cada log
                    const isDarkTheme = detectarTemaOscuro();
                    
                    const fecha = log.fecha ? new Date(log.fecha).toLocaleString('es-ES') : 'N/A';
                    const accionClass = log.accion.includes('Crear') ? 'accion-crear' : 
                                       log.accion.includes('Modificar') ? 'accion-modificar' : 
                                       log.accion.includes('Eliminar') ? 'accion-eliminar' : '';
                    
                    // Generar HTML para cambios detallados
                    let cambiosHtml = '';
                    if (log.cambios_detallados && Array.isArray(log.cambios_detallados) && log.cambios_detallados.length > 0) {
                        // Separar cambios por tipo: Factores, Montos/Cálculos, y Campos Básicos
                        const cambiosFactores = [];
                        const cambiosMontos = [];
                        const cambiosCalculo = [];
                        const cambiosBasicos = [];
                        
                        log.cambios_detallados.forEach(cambio => {
                            const campo = cambio.campo || '';
                            if (campo.startsWith('Factor')) {
                                cambiosFactores.push(cambio);
                            } else if (campo.startsWith('Monto')) {
                                cambiosMontos.push(cambio);
                            } else if (campo === 'SumaBase') {
                                cambiosCalculo.push(cambio);
                            } else {
                                cambiosBasicos.push(cambio);
                            }
                        });
                        
                        // Mapeo de nombres de campos técnicos a nombres descriptivos
                        const nombresCampos = {
                            'Ejercicio': 'Ejercicio',
                            'Instrumento': 'Instrumento',
                            'Mercado': 'Mercado',
                            'Origen': 'Origen',
                            'FechaPago': 'Fecha de Pago',
                            'SecuenciaEvento': 'Secuencia de Evento',
                            'Descripcion': 'Descripción',
                            'Dividendo': 'Dividendo',
                            'ISFUT': 'ISFUT',
                            'ValorHistorico': 'Valor Histórico',
                            'FactorActualizacion': 'Factor de Actualización',
                            'Anho': 'Año',
                            'SumaBase': 'Suma Base (8-19)',
                            // Factores
                            'Factor08': 'Factor-08 (No Constitutiva de Renta No Acogido a Impto.)',
                            'Factor09': 'Factor-09 (Impto. 1ra Categ. Afecto Gl. Comp. Con Devolución)',
                            'Factor10': 'Factor-10 (Impuesto Tasa Adicional Exento Art. 21)',
                            'Factor11': 'Factor-11 (Incremento Impuesto 1ra Categoría)',
                            'Factor12': 'Factor-12 (Impto. 1ra Categ. Exento Gl. Comp. Con Devolución)',
                            'Factor13': 'Factor-13 (Impto. 1ra Categ. Afecto Gl. Comp. Sin Devolución)',
                            'Factor14': 'Factor-14 (Impto. 1ra Categ. Exento Gl. Comp. Sin Devolución)',
                            'Factor15': 'Factor-15 (Impto. Créditos pro Impuestos Externos)',
                            'Factor16': 'Factor-16 (No Constitutiva de Renta Acogido a Impto.)',
                            'Factor17': 'Factor-17 (No Constitutiva de Renta Devolución de Capital Art.17)',
                            'Factor18': 'Factor-18 (Rentas Exentas IGC/IA)',
                            'Factor19': 'Factor-19 (Montos no constit. renta)',
                            'Factor20': 'Factor-20 (Sin Derecho a Devolucion)',
                            'Factor21': 'Factor-21 (Con Derecho a Devolucion)',
                            'Factor22': 'Factor-22 (Sin Derecho a Devolucion)',
                            'Factor23': 'Factor-23 (Con Derecho a Devolucion)',
                            'Factor24': 'Factor-24 (Sin Derecho a Devolucion)',
                            'Factor25': 'Factor-25 (Con Derecho a Devolucion)',
                            'Factor26': 'Factor-26 (Sin Derecho a Devolucion)',
                            'Factor27': 'Factor-27 (Con Derecho a Devolucion)',
                            'Factor28': 'Factor-28 (Credito por IPE)',
                            'Factor29': 'Factor-29 (Sin Derecho a Devolucion)',
                            'Factor30': 'Factor-30 (Con Derecho a Devolucion)',
                            'Factor31': 'Factor-31 (Sin Derecho a Devolucion)',
                            'Factor32': 'Factor-32 (Con Derecho a Devolucion)',
                            'Factor33': 'Factor-33 (Credito por IPE)',
                            'Factor34': 'Factor-34 (Cred. Por Impto. Tasa Adicional, Ex Art. 21 LIR)',
                            'Factor35': 'Factor-35 (Tasa Efectiva Del Cred. Del FUT TEF)',
                            'Factor36': 'Factor-36 (Tasa Efectiva Del Cred. Del FUNT TEX)',
                            'Factor37': 'Factor-37 (Devolucion de Capital Art. 17 num 7 LIR)',
                            // Montos
                            'Monto08': 'Monto-08 (No Constitutiva de Renta No Acogido a Impto.)',
                            'Monto09': 'Monto-09 (Impto. 1ra Categ. Afecto Gl. Comp. Con Devolución)',
                            'Monto10': 'Monto-10 (Impuesto Tasa Adicional Exento Art. 21)',
                            'Monto11': 'Monto-11 (Incremento Impuesto 1ra Categoría)',
                            'Monto12': 'Monto-12 (Impto. 1ra Categ. Exento Gl. Comp. Con Devolución)',
                            'Monto13': 'Monto-13 (Impto. 1ra Categ. Afecto Gl. Comp. Sin Devolución)',
                            'Monto14': 'Monto-14 (Impto. 1ra Categ. Exento Gl. Comp. Sin Devolución)',
                            'Monto15': 'Monto-15 (Impto. Créditos pro Impuestos Externos)',
                            'Monto16': 'Monto-16 (No Constitutiva de Renta Acogido a Impto.)',
                            'Monto17': 'Monto-17 (No Constitutiva de Renta Devolución de Capital Art.17)',
                            'Monto18': 'Monto-18 (Rentas Exentas IGC/IA)',
                            'Monto19': 'Monto-19 (Montos no constit. renta)',
                            'Monto20': 'Monto-20 (Sin Derecho a Devolucion)',
                            'Monto21': 'Monto-21 (Con Derecho a Devolucion)',
                            'Monto22': 'Monto-22 (Sin Derecho a Devolucion)',
                            'Monto23': 'Monto-23 (Con Derecho a Devolucion)',
                            'Monto24': 'Monto-24 (Sin Derecho a Devolucion)',
                            'Monto25': 'Monto-25 (Con Derecho a Devolucion)',
                            'Monto26': 'Monto-26 (Sin Derecho a Devolucion)',
                            'Monto27': 'Monto-27 (Con Derecho a Devolucion)',
                            'Monto28': 'Monto-28 (Credito por IPE)',
                            'Monto29': 'Monto-29 (Sin Derecho a Devolucion)',
                            'Monto30': 'Monto-30 (Con Derecho a Devolucion)',
                            'Monto31': 'Monto-31 (Sin Derecho a Devolucion)',
                            'Monto32': 'Monto-32 (Con Derecho a Devolucion)',
                            'Monto33': 'Monto-33 (Credito por IPE)',
                            'Monto34': 'Monto-34 (Cred. Por Impto. Tasa Adicional, Ex Art. 21 LIR)',
                            'Monto35': 'Monto-35 (Tasa Efectiva Del Cred. Del FUT TEF)',
                            'Monto36': 'Monto-36 (Tasa Efectiva Del Cred. Del FUNT TEX)',
                            'Monto37': 'Monto-37 (Devolucion de Capital Art. 17 num 7 LIR)'
                        };
                        
                        // Colores para tema oscuro y claro
                        const coloresTema = {
                            claro: {
                                cambioItem: '#f8f9fa',
                                codeBg: '#fff',
                                codeBorder: '#e0e0e0',
                                anterior: '#dc3545',
                                nuevo: '#28a745',
                                texto: '#1A1A1A'
                            },
                            oscuro: {
                                cambioItem: '#2D2D2D',
                                codeBg: '#1E1E1E',
                                codeBorder: '#404040',
                                anterior: '#ef5350',
                                nuevo: '#66bb6a',
                                texto: '#E0E0E0'
                            }
                        };
                        const colores = isDarkTheme ? coloresTema.oscuro : coloresTema.claro;
                        
                        // Función auxiliar para generar HTML de un cambio
                        const generarCambioHTML = (cambio, tipoColor) => {
                            const campoTecnico = cambio.campo || 'N/A';
                            const campoNombre = nombresCampos[campoTecnico] || campoTecnico;
                            const valorAnterior = cambio.valor_anterior !== null && cambio.valor_anterior !== undefined ? cambio.valor_anterior : 'N/A';
                            const valorNuevo = cambio.valor_nuevo !== null && cambio.valor_nuevo !== undefined ? cambio.valor_nuevo : 'N/A';
                            
                            return `
                                <div style="margin-bottom: 0.75rem; padding: 0.75rem; background-color: ${colores.cambioItem}; border-left: 3px solid ${tipoColor}; border-radius: 4px;">
                                    <strong style="color: ${tipoColor}; font-size: 0.9rem; display: block; margin-bottom: 0.5rem;">${campoNombre}</strong>
                                    <div style="font-size: 0.85rem; line-height: 1.6;">
                                        <div style="margin-bottom: 0.25rem;">
                                            <span style="color: ${colores.anterior}; font-weight: 600;">Anterior:</span> 
                                            <code style="background: ${colores.codeBg}; padding: 3px 6px; border-radius: 3px; border: 1px solid ${colores.codeBorder}; display: inline-block; margin-left: 0.25rem; font-family: monospace; color: ${colores.texto};">${valorAnterior}</code>
                                        </div>
                                        <div>
                                            <span style="color: ${colores.nuevo}; font-weight: 600;">Nuevo:</span> 
                                            <code style="background: ${colores.codeBg}; padding: 3px 6px; border-radius: 3px; border: 1px solid ${colores.codeBorder}; display: inline-block; margin-left: 0.25rem; font-family: monospace; color: ${colores.texto};">${valorNuevo}</code>
                                        </div>
                                    </div>
                                </div>
                            `;
                        };
                        
                        // Colores de secciones según el tema
                        const coloresSecciones = {
                            claro: {
                                calculo: { bg: 'linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%)', border: '#2196F3', texto: '#1976D2' },
                                montos: { bg: 'linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%)', border: '#FF9800', texto: '#F57C00' },
                                factores: { bg: 'linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%)', border: '#4CAF50', texto: '#2E7D32' },
                                basicos: { bg: 'linear-gradient(135deg, #F3E5F5 0%, #E1BEE7 100%)', border: '#9C27B0', texto: '#7B1FA2' }
                            },
                            oscuro: {
                                calculo: { bg: 'linear-gradient(135deg, #1a3a4a 0%, #0d2a3a 100%)', border: '#64B5F6', texto: '#90CAF9' },
                                montos: { bg: 'linear-gradient(135deg, #4a3a1a 0%, #2a1a0a 100%)', border: '#FFB74D', texto: '#FFCC80' },
                                factores: { bg: 'linear-gradient(135deg, #1e3a1e 0%, #0d2a0d 100%)', border: '#81C784', texto: '#A5D6A7' },
                                basicos: { bg: 'linear-gradient(135deg, #3a1a3a 0%, #2a0d2a 100%)', border: '#BA68C8', texto: '#CE93D8' }
                            }
                        };
                        const secciones = isDarkTheme ? coloresSecciones.oscuro : coloresSecciones.claro;
                        
                        cambiosHtml = '<div style="max-width: 700px;">';
                        
                        // Sección: Cambios en Cálculo (SumaBase)
                        if (cambiosCalculo.length > 0) {
                            cambiosHtml += `
                                <div style="margin-bottom: 1.5rem; padding: 1rem; background: ${secciones.calculo.bg}; border-radius: 6px; border: 2px solid ${secciones.calculo.border};">
                                    <h4 style="margin: 0 0 0.75rem 0; color: ${secciones.calculo.texto}; font-size: 1rem; font-weight: 600;">Cambios en el Cálculo</h4>
                            `;
                            cambiosCalculo.forEach(cambio => {
                                cambiosHtml += generarCambioHTML(cambio, secciones.calculo.border);
                            });
                            cambiosHtml += '</div>';
                        }
                        
                        // Sección: Cambios en Montos
                        if (cambiosMontos.length > 0) {
                            cambiosHtml += `
                                <div style="margin-bottom: 1.5rem; padding: 1rem; background: ${secciones.montos.bg}; border-radius: 6px; border: 2px solid ${secciones.montos.border};">
                                    <h4 style="margin: 0 0 0.75rem 0; color: ${secciones.montos.texto}; font-size: 1rem; font-weight: 600;">Cambios en Montos (Valores Ingresados)</h4>
                            `;
                            cambiosMontos.forEach(cambio => {
                                cambiosHtml += generarCambioHTML(cambio, secciones.montos.border);
                            });
                            cambiosHtml += '</div>';
                        }
                        
                        // Sección: Cambios en Factores
                        if (cambiosFactores.length > 0) {
                            cambiosHtml += `
                                <div style="margin-bottom: 1.5rem; padding: 1rem; background: ${secciones.factores.bg}; border-radius: 6px; border: 2px solid ${secciones.factores.border};">
                                    <h4 style="margin: 0 0 0.75rem 0; color: ${secciones.factores.texto}; font-size: 1rem; font-weight: 600;">Cambios en Factores (Valores Calculados)</h4>
                            `;
                            cambiosFactores.forEach(cambio => {
                                cambiosHtml += generarCambioHTML(cambio, secciones.factores.border);
                            });
                            cambiosHtml += '</div>';
                        }
                        
                        // Sección: Cambios en Campos Básicos
                        if (cambiosBasicos.length > 0) {
                            cambiosHtml += `
                                <div style="margin-bottom: 1.5rem; padding: 1rem; background: ${secciones.basicos.bg}; border-radius: 6px; border: 2px solid ${secciones.basicos.border};">
                                    <h4 style="margin: 0 0 0.75rem 0; color: ${secciones.basicos.texto}; font-size: 1rem; font-weight: 600;">Cambios en Campos Básicos</h4>
                            `;
                            cambiosBasicos.forEach(cambio => {
                                cambiosHtml += generarCambioHTML(cambio, secciones.basicos.border);
                            });
                            cambiosHtml += '</div>';
                        }
                        
                        cambiosHtml += '</div>';
                    } else {
                        cambiosHtml = `<span style="color: ${isDarkTheme ? '#B0B0B0' : '#999'}; font-style: italic;">Sin cambios detallados</span>`;
                    }
                    
                    html += `
                        <tr>
                            <td>${fecha}</td>
                            <td>
                                ${log.actor_nombre && log.actor_nombre !== 'N/A' ? `<strong>${log.actor_nombre}</strong><br>` : ''}
                                ${log.actor_correo || 'N/A'}<br>
                                <small style="color: ${isDarkTheme ? '#B0B0B0' : '#666'};">ID: ${log.actor_id || 'N/A'}</small>
                            </td>
                            <td>
                                <span class="accion-badge ${accionClass}">${log.accion || 'N/A'}</span>
                            </td>
                            <td style="max-width: 700px; word-wrap: break-word; min-width: 600px;">
                                ${cambiosHtml}
                            </td>
                        </tr>
                    `;
                });
                tbody.innerHTML = html;
            } else {
                // Detectar tema oscuro dinámicamente
                const isDarkTheme = detectarTemaOscuro();
                tbody.innerHTML = `
                    <tr>
                        <td colspan="4" style="text-align: center; padding: 40px; color: ${isDarkTheme ? '#B0B0B0' : '#999'};">
                            No hay registros de log para esta calificación.
                        </td>
                    </tr>
                `;
            }
        }

        // Mostrar modal
        modalOverlay.style.display = 'flex';
    }

    // ========== BOTÓN LIMPIAR ==========
    // Cargar todas las calificaciones al iniciar (siempre hacer búsqueda fresca para mostrar datos actualizados)
    // Esto asegura que incluso si el usuario navega a otro módulo y regresa, se muestren los datos más recientes
    if (btnBuscar && buscarCalificacionesUrl) {
        // Resetear filtros para mostrar todas las calificaciones
        if (dashboardMercado) dashboardMercado.value = '';
        if (dashboardOrigen) dashboardOrigen.value = '';
        if (dashboardPeriodo) dashboardPeriodo.value = '';
        // Hacer búsqueda automática al cargar para obtener datos frescos
        btnBuscar.click();
    } else if (window.CALIFICACIONES_INICIALES && window.CALIFICACIONES_INICIALES.length > 0) {
        // Fallback: usar calificaciones iniciales solo si no se puede hacer búsqueda
        renderizarCalificaciones(window.CALIFICACIONES_INICIALES);
    }
    
    if (btnLimpiar) {
        btnLimpiar.addEventListener('click', function() {
            // Resetear filtros a valores vacíos para limpiar todos los filtros
            if (dashboardMercado) dashboardMercado.value = ''; // Vacío para mostrar todos
            if (dashboardOrigen) dashboardOrigen.value = ''; // Vacío para mostrar todos
            if (dashboardPeriodo) dashboardPeriodo.value = ''; // Vacío para mostrar todos

            // Ejecutar búsqueda automáticamente para mostrar todas las calificaciones sin filtros
            if (btnBuscar) {
                btnBuscar.click();
            }
        });
    }
    
    // ========== MODAL DE EXPORTAR CALIFICACIONES ==========
    const modalExportarOverlay = document.getElementById('exportar-modal-overlay');
    const btnCerrarExportar = document.getElementById('btn-cerrar-exportar');
    const btnCerrarExportarX = document.getElementById('btn-cerrar-exportar-x');
    const btnExportarSeleccionadas = document.getElementById('btn-exportar-seleccionadas');
    const checkboxTodasExportar = document.getElementById('checkbox-todas-exportar');
    const exportarCalificacionesList = document.getElementById('exportar-calificaciones-list');
    const exportarContador = document.getElementById('exportar-contador');
    
    let calificacionesFiltradas = []; // Almacenar las calificaciones filtradas para el modal
    
    // Función para cargar las calificaciones filtradas del dashboard en el modal
    // ============================================
    // FUNCIÓN: cargarCalificacionesParaExportar()
    // ============================================
    /**
     * Carga las calificaciones disponibles para exportar según los filtros del dashboard.
     * 
     * POR QUÉ ESTA FUNCIÓN ES NECESARIA:
     * - Permite seleccionar calificaciones específicas para exportar
     * - Usa los mismos filtros que el dashboard (consistencia)
     * - Muestra indicador de carga mientras obtiene datos
     * - Actualiza la lista de calificaciones disponibles
     * 
     * CÓMO FUNCIONA:
     * 1. Muestra indicador de carga
     * 2. Obtiene filtros actuales del dashboard (mercado, origen, período)
     * 3. Envía petición AJAX al servidor con los filtros
     * 4. El servidor retorna calificaciones filtradas
     * 5. Guarda calificaciones en variable global
     * 6. Llama a renderizarListaExportar() para mostrarlas
     */
    function cargarCalificacionesParaExportar() {
        if (!exportarCalificacionesList) return;
        
        exportarCalificacionesList.innerHTML = '<div class="exportar-loading"><i class="bi bi-hourglass-split"></i><p>Cargando calificaciones...</p></div>';
        
        // Obtener los filtros actuales del dashboard
        const mercado = dashboardMercado ? dashboardMercado.value : '';
        const origen = dashboardOrigen ? dashboardOrigen.value : '';
        const periodo = dashboardPeriodo ? dashboardPeriodo.value : '';
        
        // Construir URL con los mismos filtros que el dashboard
        const buscarCalificacionesUrl = window.DJANGO_URLS?.buscarCalificaciones || '/prueba/buscar-calificaciones/';
        const params = new URLSearchParams();
        if (mercado) params.append('mercado', mercado);
        if (origen) params.append('origen', origen);
        if (periodo) params.append('periodo', periodo);
        
        const url = params.toString() ? `${buscarCalificacionesUrl}?${params.toString()}` : buscarCalificacionesUrl;
        
        fetch(url, {
            method: 'GET',
            headers: {
                'X-CSRFToken': csrftoken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.calificaciones) {
                calificacionesFiltradas = data.calificaciones;
                renderizarListaExportar();
            } else {
                exportarCalificacionesList.innerHTML = '<div class="exportar-loading"><i class="bi bi-exclamation-triangle"></i><p>No se pudieron cargar las calificaciones</p></div>';
            }
        })
        .catch(error => {
            console.error('Error al cargar calificaciones:', error);
            exportarCalificacionesList.innerHTML = '<div class="exportar-loading"><i class="bi bi-x-circle" style="color: var(--color-danger);"></i><p style="color: var(--color-danger);">Error al cargar calificaciones</p></div>';
        });
    }
    
    // ============================================
    // FUNCIÓN: renderizarListaExportar()
    // ============================================
    /**
     * Renderiza la lista de calificaciones en el modal de exportar con checkboxes.
     * 
     * POR QUÉ ESTA FUNCIÓN ES ÚTIL:
     * - Muestra calificaciones disponibles para exportar
     * - Permite seleccionar múltiples calificaciones con checkboxes
     * - Muestra información básica de cada calificación
     * - Agrega event listeners para manejar selecciones
     * 
     * CÓMO FUNCIONA:
     * 1. Valida que existan calificaciones para mostrar
     * 2. Genera HTML para cada calificación con checkbox
     * 3. Muestra información básica (instrumento, ejercicio, mercado, origen)
     * 4. Inserta HTML en el contenedor
     * 5. Agrega event listeners a checkboxes y items
     * 6. Actualiza contador de seleccionadas
     */
    function renderizarListaExportar() {
        if (!exportarCalificacionesList || calificacionesFiltradas.length === 0) {
            exportarCalificacionesList.innerHTML = '<div class="exportar-loading"><i class="bi bi-inbox"></i><p>No hay calificaciones disponibles con los filtros actuales</p></div>';
            return;
        }
        
        let html = '';
        calificacionesFiltradas.forEach((cal, index) => {
            const calId = cal.id || cal._id || '';
            html += `
                <div class="opcion-item opcion-item-exportar" data-index="${index}">
                    <input type="checkbox" id="checkbox-exportar-${index}" class="checkbox-exportar-calificacion" data-cal-id="${calId}">
                    <div>
                        <div>${cal.instrumento || 'Sin instrumento'}</div>
                        <div>
                            <span><strong>Ejercicio:</strong> ${cal.ejercicio || 'N/A'}</span>
                            <span><strong>Mercado:</strong> ${cal.mercado || 'N/A'}</span>
                            <span><strong>Origen:</strong> ${cal.origen || 'N/A'}</span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        exportarCalificacionesList.innerHTML = html;
        
        // Agregar event listeners a los checkboxes después de renderizar
        const checkboxes = exportarCalificacionesList.querySelectorAll('.checkbox-exportar-calificacion');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function(e) {
                e.stopPropagation(); // Evitar que el evento se propague al item
                actualizarContadorExportar();
            });
            checkbox.addEventListener('click', function(e) {
                e.stopPropagation(); // Evitar que el evento se propague al item
            });
        });
        
        // Agregar event listeners a los items para hacer clic en el checkbox
        const items = exportarCalificacionesList.querySelectorAll('.opcion-item-exportar');
        items.forEach(item => {
            item.addEventListener('click', function(e) {
                // Si el clic fue directamente en el checkbox, no hacer nada más (ya se maneja arriba)
                if (e.target.type === 'checkbox') {
                    return;
                }
                // Si el clic fue en el item, hacer toggle del checkbox
                const checkbox = item.querySelector('.checkbox-exportar-calificacion');
                if (checkbox) {
                    checkbox.checked = !checkbox.checked;
                    // Disparar evento change manualmente para que se actualice el contador
                    checkbox.dispatchEvent(new Event('change'));
                }
            });
        });
        
        actualizarContadorExportar();
    }
    
    // Función para actualizar el contador de calificaciones seleccionadas
    // ============================================
    // FUNCIÓN: actualizarContadorExportar()
    // ============================================
    /**
     * Actualiza el contador de calificaciones seleccionadas para exportar.
     * 
     * POR QUÉ ESTA FUNCIÓN ES ÚTIL:
     * - Muestra cuántas calificaciones están seleccionadas
     * - Actualiza el icono según la cantidad (vacío o con check)
     * - Habilita/deshabilita el botón de exportar según la selección
     * - Actualiza el checkbox "Todas" si todas están seleccionadas
     * 
     * CÓMO FUNCIONA:
     * 1. Cuenta cuántos checkboxes están marcados
     * 2. Actualiza el texto del contador
     * 3. Cambia el icono según la cantidad (vacío o con check)
     * 4. Habilita/deshabilita el botón de exportar
     * 5. Actualiza el estado del checkbox "Todas"
     */
    function actualizarContadorExportar() {
        if (!exportarContador) return;
        
        const checkboxes = document.querySelectorAll('.checkbox-exportar-calificacion:checked');
        const count = checkboxes.length;
        
        const contadorText = exportarContador.querySelector('.exportar-contador-text');
        if (contadorText) {
            contadorText.textContent = `${count} calificación${count !== 1 ? 'es' : ''} seleccionada${count !== 1 ? 's' : ''}`;
        } else {
            exportarContador.textContent = `${count} calificación${count !== 1 ? 'es' : ''} seleccionada${count !== 1 ? 's' : ''}`;
        }
        
        // Actualizar icono según cantidad
        const contadorIcon = exportarContador.querySelector('i');
        if (contadorIcon) {
            if (count > 0) {
                contadorIcon.className = 'bi bi-check-circle-fill';
                contadorIcon.style.color = 'var(--color-success)';
            } else {
                contadorIcon.className = 'bi bi-check-circle';
                contadorIcon.style.color = 'var(--color-primary)';
            }
        }
        
        // Habilitar/deshabilitar botón de exportar
        if (btnExportarSeleccionadas) {
            btnExportarSeleccionadas.disabled = count === 0;
        }
        
        // Actualizar checkbox "Todas"
        if (checkboxTodasExportar) {
            const totalCheckboxes = document.querySelectorAll('.checkbox-exportar-calificacion').length;
            checkboxTodasExportar.checked = count === totalCheckboxes && totalCheckboxes > 0;
        }
    }
    
    // ============================================
    // FUNCIÓN: abrirModalExportar()
    // ============================================
    /**
     * Abre el modal de exportar calificaciones.
     * 
     * POR QUÉ ESTA FUNCIÓN ES NECESARIA:
     * - Permite al usuario seleccionar calificaciones para exportar
     * - Carga las calificaciones disponibles según filtros
     * - Muestra el modal con la lista de calificaciones
     * 
     * CÓMO FUNCIONA:
     * 1. Muestra el modal cambiando display a 'flex'
     * 2. Carga calificaciones disponibles llamando a cargarCalificacionesParaExportar()
     */
    function abrirModalExportar() {
        if (modalExportarOverlay) {
            modalExportarOverlay.style.display = 'flex';
            cargarCalificacionesParaExportar();
        }
    }
    
    // ============================================
    // FUNCIÓN: cerrarModalExportar()
    // ============================================
    /**
     * Cierra el modal de exportar calificaciones y limpia las selecciones.
     * 
     * POR QUÉ ESTA FUNCIÓN ES NECESARIA:
     * - Permite cerrar el modal cuando el usuario termina
     * - Limpia las selecciones para la próxima vez
     * - Oculta el overlay y el contenido del modal
     * 
     * CÓMO FUNCIONA:
     * 1. Oculta el modal cambiando display a 'none'
     * 2. Desmarca el checkbox "Todas"
     * 3. Desmarca todos los checkboxes individuales
     * 4. Actualiza el contador
     */
    function cerrarModalExportar() {
        if (modalExportarOverlay) {
            modalExportarOverlay.style.display = 'none';
            // Limpiar selecciones
            if (checkboxTodasExportar) checkboxTodasExportar.checked = false;
            const checkboxes = document.querySelectorAll('.checkbox-exportar-calificacion');
            checkboxes.forEach(cb => cb.checked = false);
            actualizarContadorExportar();
        }
    }
    
    // Event listeners para el modal de exportar
    if (btnExportar) {
        btnExportar.addEventListener('click', abrirModalExportar);
    }
    
    if (btnCerrarExportar) {
        btnCerrarExportar.addEventListener('click', cerrarModalExportar);
    }
    
    if (btnCerrarExportarX) {
        btnCerrarExportarX.addEventListener('click', cerrarModalExportar);
    }
    
    // Checkbox "Todas" - seleccionar/deseleccionar todas
    if (checkboxTodasExportar) {
        checkboxTodasExportar.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.checkbox-exportar-calificacion');
            checkboxes.forEach(cb => {
                cb.checked = checkboxTodasExportar.checked;
            });
            actualizarContadorExportar();
        });
    }
    
    // Botón exportar seleccionadas
    if (btnExportarSeleccionadas) {
        btnExportarSeleccionadas.addEventListener('click', function() {
            const checkboxes = document.querySelectorAll('.checkbox-exportar-calificacion:checked');
            const ids = Array.from(checkboxes).map(cb => cb.getAttribute('data-cal-id')).filter(id => id);
            
            if (ids.length === 0) {
                mostrarMensaje('Advertencia', 'Debe seleccionar al menos una calificación para exportar', 'warning');
                return;
            }
            
            // Construir URL con los IDs
            const exportarUrl = window.DJANGO_URLS?.exportarCalificaciones || '/prueba/exportar-calificaciones/';
            const params = new URLSearchParams();
            params.append('ids', ids.join(','));
            
            const url = `${exportarUrl}?${params.toString()}`;
            
            // Cerrar modal y exportar
            cerrarModalExportar();
            
            // Abrir en nueva ventana para descargar el archivo
            window.open(url, '_blank');
        });
    }

    // ========== MODALES DE CARGA DE ARCHIVOS ==========
    
    // Variables para almacenar datos del CSV
    let datosCSVFactor = null;
    let datosCSVMonto = null;
    let hashArchivoFactor = null;
    let nombreArchivoFactorData = null;
    let hashArchivoMonto = null;
    let nombreArchivoMontoData = null;
    
    // Elementos del modal de carga por factor
    const modalCargaFactor = document.getElementById('carga-factor-modal-overlay');
    const btnCargaFactor = document.getElementById('btn-carga-factor');
    const btnCerrarCargaFactor = document.getElementById('btn-cerrar-carga-factor-x');
    const btnCancelarFactor = document.getElementById('btn-cancelar-factor');
    const btnSeleccionarArchivoFactor = document.getElementById('btn-seleccionar-archivo-factor');
    const inputArchivoFactor = document.getElementById('archivo-factor-input');
    const nombreArchivoFactor = document.getElementById('archivo-factor-nombre');
    const tablaPreviewFactor = document.getElementById('tabla-preview-factor-body');
    const btnGrabarFactor = document.getElementById('btn-grabar-factor');
    const btnVerFormatoFactor = document.getElementById('btn-ver-formato-factor');
    
    // Elementos del modal de carga por monto
    const modalCargaMonto = document.getElementById('carga-monto-modal-overlay');
    const btnCargaMonto = document.getElementById('btn-carga-monto');
    const btnCerrarCargaMonto = document.getElementById('btn-cerrar-carga-monto-x');
    const btnCancelarMonto = document.getElementById('btn-cancelar-monto');
    const btnSeleccionarArchivoMonto = document.getElementById('btn-seleccionar-archivo-monto');
    const inputArchivoMonto = document.getElementById('archivo-monto-input');
    const nombreArchivoMonto = document.getElementById('archivo-monto-nombre');
    const tablaPreviewMonto = document.getElementById('tabla-preview-monto-body');
    const btnCalcularFactoresMonto = document.getElementById('btn-calcular-factores-monto');
    const btnGrabarMonto = document.getElementById('btn-grabar-monto');
    const btnVerFormatoMonto = document.getElementById('btn-ver-formato-monto');
    
    // Abrir modal de carga por factor
    if (btnCargaFactor) {
        btnCargaFactor.addEventListener('click', () => {
            // Limpiar el modal antes de abrirlo
            limpiarModalFactor();
            if (modalCargaFactor) modalCargaFactor.style.display = 'flex';
        });
    }
    
    // Abrir modal de carga por monto
    if (btnCargaMonto) {
        btnCargaMonto.addEventListener('click', () => {
            // Limpiar el modal antes de abrirlo
            limpiarModalMonto();
            if (modalCargaMonto) modalCargaMonto.style.display = 'flex';
        });
    }
    
    // Cerrar modales
    if (btnCerrarCargaFactor) {
        btnCerrarCargaFactor.addEventListener('click', () => {
            if (modalCargaFactor) modalCargaFactor.style.display = 'none';
            limpiarModalFactor();
        });
    }
    
    if (btnCancelarFactor) {
        btnCancelarFactor.addEventListener('click', () => {
            if (modalCargaFactor) modalCargaFactor.style.display = 'none';
            limpiarModalFactor();
        });
    }
    
    if (btnCerrarCargaMonto) {
        btnCerrarCargaMonto.addEventListener('click', () => {
            if (modalCargaMonto) modalCargaMonto.style.display = 'none';
            limpiarModalMonto();
        });
    }
    
    if (btnCancelarMonto) {
        btnCancelarMonto.addEventListener('click', () => {
            if (modalCargaMonto) modalCargaMonto.style.display = 'none';
            limpiarModalMonto();
        });
    }
    
    // Seleccionar archivo - Factor
    if (btnSeleccionarArchivoFactor && inputArchivoFactor) {
        btnSeleccionarArchivoFactor.addEventListener('click', () => {
            inputArchivoFactor.click();
        });
        
        inputArchivoFactor.addEventListener('change', (e) => {
            const archivo = e.target.files[0];
            if (archivo) {
                nombreArchivoFactor.value = archivo.name;
                leerArchivoCSV(archivo, 'factor');
            }
        });
    }
    
    // Seleccionar archivo - Monto
    if (btnSeleccionarArchivoMonto && inputArchivoMonto) {
        btnSeleccionarArchivoMonto.addEventListener('click', () => {
            inputArchivoMonto.click();
        });
        
        
        inputArchivoMonto.addEventListener('change', (e) => {
            const archivo = e.target.files[0];
            if (archivo) {
                nombreArchivoMonto.value = archivo.name;
                leerArchivoCSV(archivo, 'monto');
            }
        });
    }
    
    // ============================================
    // FUNCIÓN: leerArchivoCSV(archivo, tipo)
    // ============================================
    /**
     * Lee un archivo CSV y lo envía al servidor para previsualización.
     * 
     * POR QUÉ ESTA FUNCIÓN ES CRÍTICA:
     * - Permite cargar archivos CSV con calificaciones en masa
     * - Valida el formato del archivo antes de guardar
     * - Detecta archivos duplicados usando hash SHA-256
     * - Muestra previsualización para que el usuario revise antes de confirmar
     * 
     * CÓMO FUNCIONA:
     * 1. Valida que se haya seleccionado un archivo
     * 2. Crea FormData con el archivo y el tipo (factor o monto)
     * 3. Envía petición AJAX al servidor para previsualizar
     * 4. El servidor lee el CSV, calcula hash, valida formato
     * 5. Si es exitoso, muestra previsualización en tabla
     * 6. Si hay errores, muestra mensajes apropiados
     * 
     * DETECCIÓN DE DUPLICADOS:
     * - El servidor calcula hash SHA-256 del contenido
     * - Compara con archivos ya subidos
     * - Previene cargar el mismo archivo múltiples veces
     * 
     * Parámetros:
     *   - archivo: Objeto File del archivo CSV seleccionado
     *   - tipo: Tipo de carga ('factor' o 'monto')
     *     - 'factor': CSV con factores ya calculados
     *     - 'monto': CSV con montos (se calcularán factores después)
     */
    function leerArchivoCSV(archivo, tipo) {
        if (!archivo) {
            mostrarMensaje('Error', 'No se seleccionó ningún archivo', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('archivo', archivo);
        formData.append('tipo', tipo);
        
        const url = tipo === 'factor' 
            ? (window.DJANGO_URLS?.previewFactor || '/prueba/preview-factor/')
            : (window.DJANGO_URLS?.previewMonto || '/prueba/preview-monto/');
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            body: formData
        })
        .then(response => {
            // Intentar parsear JSON incluso si el status no es 200
            return response.json().then(data => {
                return { status: response.status, ok: response.ok, data: data };
            }).catch(() => {
                // Si no se puede parsear JSON, retornar error genérico
                return { status: response.status, ok: response.ok, data: { success: false, error: 'Error al procesar la respuesta del servidor' } };
            });
        })
        .then(result => {
            const data = result.data;
            if (data.success) {
                if (tipo === 'factor') {
                    datosCSVFactor = data.datos;
                    hashArchivoFactor = data.hash_archivo || null;
                    nombreArchivoFactorData = data.nombre_archivo || null;
                    mostrarPreviewFactor(data.datos);
                    if (btnGrabarFactor) btnGrabarFactor.disabled = false;
                } else {
                    datosCSVMonto = data.datos;
                    hashArchivoMonto = data.hash_archivo || null;
                    nombreArchivoMontoData = data.nombre_archivo || null;
                    mostrarPreviewMonto(data.datos);
                    if (btnCalcularFactoresMonto) btnCalcularFactoresMonto.disabled = false;
                }
                
                if (data.errores && data.errores.length > 0) {
                    mostrarMensaje('Advertencia', `Se encontraron ${data.errores.length} error(es) en el archivo. Revise el formato.`, 'warning');
                }
            } else {
                // Si hay error de duplicado, mostrar mensaje específico
                if (data.duplicado) {
                    mostrarMensaje('Archivo Duplicado', data.error || 'Este archivo ya fue subido anteriormente', 'error');
                } else {
                    mostrarMensaje('Error', data.error || 'Error al procesar el archivo', 'error');
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarMensaje('Error', 'Error al procesar el archivo. Por favor, intente nuevamente.', 'error');
        });
    }
    
    // ============================================
    // FUNCIÓN: mostrarPreviewFactor(datos)
    // ============================================
    /**
     * Muestra una previsualización de los datos CSV con factores en una tabla.
     * 
     * POR QUÉ ESTA FUNCIÓN ES ÚTIL:
     * - Permite al usuario revisar los datos antes de guardar
     * - Muestra factores ya calculados del CSV
     * - Valida visualmente que los datos sean correctos
     * 
     * CÓMO FUNCIONA:
     * 1. Valida que exista el elemento tablaPreviewFactor
     * 2. Si no hay datos, muestra mensaje informativo
     * 3. Genera HTML para cada fila del CSV
     * 4. Muestra datos básicos y factores F8 a F37
     * 5. Inserta el HTML en la tabla de previsualización
     * 
     * Parámetros:
     *   - datos: Array de objetos con datos del CSV (cada objeto es una fila)
     */
    function mostrarPreviewFactor(datos) {
        if (!tablaPreviewFactor) return;
        
        if (datos.length === 0) {
            tablaPreviewFactor.innerHTML = '<tr><td colspan="38" style="padding: 2rem; text-align: center; color: #999;">No hay datos para mostrar.</td></tr>';
            return;
        }
        
        let html = '';
        datos.forEach((fila, index) => {
            html += '<tr>';
            html += `<td>${fila.Ejercicio || ''}</td>`;
            html += `<td>${fila.Mercado || ''}</td>`;
            html += `<td>${fila.Instrumento || ''}</td>`;
            html += `<td>${fila.FEC_PAGO || ''}</td>`;
            html += `<td>${fila.SEC_EVE || ''}</td>`;
            html += `<td>${fila.DESCRIPCION || ''}</td>`;
            
            // Factores F8 a F37
            for (let i = 8; i <= 37; i++) {
                const factorKey = `F${i}`;
                html += `<td>${fila[factorKey] || '0.0'}</td>`;
            }
            
            html += '</tr>';
        });
        
        tablaPreviewFactor.innerHTML = html;
    }
    
    // ============================================
    // FUNCIÓN: mostrarPreviewMonto(datos)
    // ============================================
    /**
     * Muestra una previsualización de los datos CSV con montos en una tabla.
     * 
     * POR QUÉ ESTA FUNCIÓN ES ÚTIL:
     * - Permite al usuario revisar los montos antes de calcular factores
     * - Muestra montos del CSV (F8 MONT a F37 MONT)
     * - Valida visualmente que los datos sean correctos
     * 
     * CÓMO FUNCIONA:
     * 1. Valida que exista el elemento tablaPreviewMonto
     * 2. Si no hay datos, muestra mensaje informativo
     * 3. Genera HTML para cada fila del CSV
     * 4. Muestra datos básicos y montos F8 MONT a F37 MONT
     * 5. Inserta el HTML en la tabla de previsualización
     * 
     * Parámetros:
     *   - datos: Array de objetos con datos del CSV (cada objeto es una fila)
     */
    function mostrarPreviewMonto(datos) {
        if (!tablaPreviewMonto) return;
        
        if (datos.length === 0) {
            tablaPreviewMonto.innerHTML = '<tr><td colspan="38" style="padding: 2rem; text-align: center; color: #999;">No hay datos para mostrar.</td></tr>';
            return;
        }
        
        let html = '';
        datos.forEach((fila, index) => {
            html += '<tr>';
            html += `<td>${fila.Ejercicio || ''}</td>`;
            html += `<td>${fila.Mercado || ''}</td>`;
            html += `<td>${fila.Instrumento || ''}</td>`;
            html += `<td>${fila.FEC_PAGO || ''}</td>`;
            html += `<td>${fila.SEC_EVE || ''}</td>`;
            html += `<td>${fila.DESCRIPCION || ''}</td>`;
            
            // Montos F8 MONT a F37 MONT
            for (let i = 8; i <= 37; i++) {
                const montoKey = `F${i} MONT`;
                const montoKeyAlt = `F${i} M`;
                const valor = fila[montoKey] || fila[montoKeyAlt] || '0.0';
                html += `<td>${valor}</td>`;
            }
            
            html += '</tr>';
        });
        
        tablaPreviewMonto.innerHTML = html;
    }
    
    // Función para mostrar preview con factores calculados (después de calcular)
    // ============================================
    // FUNCIÓN: mostrarPreviewMontoConFactores(datos)
    // ============================================
    /**
     * Muestra una previsualización de los datos CSV con montos y factores calculados.
     * 
     * POR QUÉ ESTA FUNCIÓN ES ÚTIL:
     * - Muestra los factores calculados después de presionar "Calcular Factores"
     * - Permite al usuario revisar los factores antes de guardar
     * - Reemplaza la vista de montos con la vista de factores
     * 
     * CÓMO FUNCIONA:
     * 1. Valida que exista el elemento tablaPreviewMonto
     * 2. Si no hay datos, muestra mensaje informativo
     * 3. Genera HTML para cada fila del CSV
     * 4. Muestra datos básicos y factores F8 a F37 (calculados)
     * 5. Inserta el HTML en la tabla de previsualización
     * 
     * DIFERENCIA CON mostrarPreviewMonto:
     * - mostrarPreviewMonto: Muestra montos (F8 MONT a F37 MONT)
     * - mostrarPreviewMontoConFactores: Muestra factores calculados (F8 a F37)
     * 
     * Parámetros:
     *   - datos: Array de objetos con datos del CSV (cada objeto es una fila con factores calculados)
     */
    function mostrarPreviewMontoConFactores(datos) {
        // Validar que el elemento tablaPreviewMonto exista
        // POR QUÉ: No podemos renderizar si no existe el contenedor
        if (!tablaPreviewMonto) return;
        
        if (datos.length === 0) {
            tablaPreviewMonto.innerHTML = '<tr><td colspan="38" style="padding: 2rem; text-align: center; color: #999;">No hay datos para mostrar.</td></tr>';
            return;
        }
        
        let html = '';
        datos.forEach((fila, index) => {
            html += '<tr>';
            html += `<td>${fila.Ejercicio || ''}</td>`;
            html += `<td>${fila.Mercado || ''}</td>`;
            html += `<td>${fila.Instrumento || ''}</td>`;
            html += `<td>${fila.FEC_PAGO || ''}</td>`;
            html += `<td>${fila.SEC_EVE || ''}</td>`;
            html += `<td>${fila.DESCRIPCION || ''}</td>`;
            
            // Factores calculados F8 a F37
            for (let i = 8; i <= 37; i++) {
                const factorKey = `F${i}`;
                const valor = fila[factorKey] || '0.0';
                html += `<td>${valor}</td>`;
            }
            
            html += '</tr>';
        });
        
        tablaPreviewMonto.innerHTML = html;
    }
    
    // ============================================
    // FUNCIÓN: limpiarModalFactor()
    // ============================================
    /**
     * Limpia todos los datos y campos del modal de carga por factores.
     * 
     * POR QUÉ ESTA FUNCIÓN ES ÚTIL:
     * - Resetea el modal cuando se cierra o se abre nuevamente
     * - Limpia variables globales de datos CSV
     * - Limpia campos del formulario
     * - Limpia la tabla de previsualización
     * - Deshabilita botones hasta que se cargue un nuevo archivo
     * 
     * CÓMO FUNCIONA:
     * 1. Limpia variables globales (datosCSVFactor, hashArchivoFactor, nombreArchivoFactorData)
     * 2. Limpia campos del formulario (input de archivo, nombre de archivo)
     * 3. Limpia la tabla de previsualización
     * 4. Deshabilita el botón de grabar
     */
    function limpiarModalFactor() {
        // Limpiar variables de datos
        datosCSVFactor = null;
        hashArchivoFactor = null;
        nombreArchivoFactorData = null;
        // Limpiar campos del formulario
        if (inputArchivoFactor) inputArchivoFactor.value = '';
        if (nombreArchivoFactor) nombreArchivoFactor.value = '';
        // Limpiar tabla de preview
        if (tablaPreviewFactor) {
            tablaPreviewFactor.innerHTML = '<tr><td colspan="38" style="padding: 2rem; text-align: center; color: #999;">No hay datos para mostrar. Seleccione un archivo CSV.</td></tr>';
        }
        // Deshabilitar botón de grabar
        if (btnGrabarFactor) btnGrabarFactor.disabled = true;
    }
    
    // ============================================
    // FUNCIÓN: limpiarModalMonto()
    // ============================================
    /**
     * Limpia todos los datos y campos del modal de carga por montos.
     * 
     * POR QUÉ ESTA FUNCIÓN ES ÚTIL:
     * - Resetea el modal cuando se cierra o se abre nuevamente
     * - Limpia variables globales de datos CSV
     * - Limpia campos del formulario
     * - Limpia la tabla de previsualización
     * - Deshabilita botones hasta que se cargue un nuevo archivo
     * 
     * CÓMO FUNCIONA:
     * 1. Limpia variables globales (datosCSVMonto, hashArchivoMonto, nombreArchivoMontoData)
     * 2. Limpia campos del formulario (input de archivo, nombre de archivo)
     * 3. Limpia la tabla de previsualización
     * 4. Deshabilita botones (calcular factores, grabar)
     */
    function limpiarModalMonto() {
        // Limpiar variables de datos
        datosCSVMonto = null;
        hashArchivoMonto = null;
        nombreArchivoMontoData = null;
        // Limpiar campos del formulario
        if (inputArchivoMonto) inputArchivoMonto.value = '';
        if (nombreArchivoMonto) nombreArchivoMonto.value = '';
        // Limpiar tabla de preview
        if (tablaPreviewMonto) {
            tablaPreviewMonto.innerHTML = '<tr><td colspan="38" style="padding: 2rem; text-align: center; color: #999;">No hay datos para mostrar. Seleccione un archivo CSV.</td></tr>';
        }
        // Deshabilitar botones
        if (btnCalcularFactoresMonto) btnCalcularFactoresMonto.disabled = true;
        if (btnGrabarMonto) btnGrabarMonto.disabled = true;
    }
    
    // Grabar datos - Factor
    if (btnGrabarFactor) {
        btnGrabarFactor.addEventListener('click', () => {
            if (!datosCSVFactor || datosCSVFactor.length === 0) {
                mostrarMensaje('Error', 'No hay datos para grabar', 'error');
                return;
            }
            
            grabarDatosCSV(datosCSVFactor, 'factor');
        });
    }
    
    // Calcular factores - Monto
    if (btnCalcularFactoresMonto) {
        btnCalcularFactoresMonto.addEventListener('click', () => {
            if (!datosCSVMonto || datosCSVMonto.length === 0) {
                mostrarMensaje('Error', 'No hay datos para calcular', 'error');
                return;
            }
            
            calcularFactoresDesdeMontos(datosCSVMonto);
        });
    }
    
    // Grabar datos - Monto
    if (btnGrabarMonto) {
        btnGrabarMonto.addEventListener('click', () => {
            if (!datosCSVMonto || datosCSVMonto.length === 0) {
                mostrarMensaje('Error', 'No hay datos para grabar', 'error');
                return;
            }
            
            grabarDatosCSV(datosCSVMonto, 'monto');
        });
    }
    
    // ============================================
    // FUNCIÓN: grabarDatosCSV(datos, tipo)
    // ============================================
    /**
     * Guarda los datos del CSV en la base de datos después de la previsualización.
     * 
     * POR QUÉ ESTA FUNCIÓN ES CRÍTICA:
     * - Es el paso final de la carga masiva de calificaciones
     * - Guarda múltiples calificaciones en una sola operación
     * - Valida datos antes de guardar en el servidor
     * - Maneja errores y muestra resultados detallados
     * - Actualiza la tabla después de guardar
     * 
     * CÓMO FUNCIONA:
     * 1. Determina la URL según el tipo (factor o monto)
     * 2. Obtiene hash y nombre del archivo guardados
     * 3. Envía datos al servidor en formato JSON
     * 4. El servidor valida y guarda cada calificación en MongoDB
     * 5. Retorna cantidad de calificaciones creadas y errores encontrados
     * 6. Muestra mensaje de éxito/error con detalles
     * 7. Cierra el modal y actualiza la tabla
     * 
     * FLUJO COMPLETO:
     * - Usuario selecciona CSV → leerArchivoCSV() → Previsualización → Esta función guarda
     * 
     * Parámetros:
     *   - datos: Array de objetos con datos del CSV (cada objeto es una fila)
     *   - tipo: Tipo de carga ('factor' o 'monto')
     */
    function grabarDatosCSV(datos, tipo) {
        const url = tipo === 'factor' 
            ? (window.DJANGO_URLS?.cargarFactor || '/prueba/cargar-factor/')
            : (window.DJANGO_URLS?.cargarMonto || '/prueba/cargar-monto/');
        
        // Obtener hash y nombre del archivo según el tipo
        const hashArchivo = tipo === 'factor' ? hashArchivoFactor : hashArchivoMonto;
        const nombreArchivo = tipo === 'factor' ? nombreArchivoFactorData : nombreArchivoMontoData;
        
        console.log('Enviando datos para grabar:', { tipo, total: datos.length, url, hashArchivo, nombreArchivo });
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                datos: datos,
                hash_archivo: hashArchivo,
                nombre_archivo: nombreArchivo
            })
        })
        .then(response => {
            console.log('Respuesta del servidor:', response.status, response.statusText);
            // Intentar parsear JSON incluso si el status no es 200 para obtener mensajes personalizados
            return response.json().then(data => {
                return { status: response.status, ok: response.ok, data: data };
            }).catch(() => {
                // Si no se puede parsear JSON, retornar error genérico
                return { status: response.status, ok: response.ok, data: { success: false, error: `Error del servidor: ${response.status} ${response.statusText}` } };
            });
        })
        .then(result => {
            const data = result.data;
            console.log('Datos recibidos del servidor:', data);
            if (data.success) {
                if (data.total > 0) {
                    let mensaje = `Se grabaron ${data.total} calificación(es) exitosamente.`;
                    if (data.errores && data.errores.length > 0) {
                        mensaje += `\n\nSe encontraron ${data.errores.length} error(es):\n${data.errores.slice(0, 5).join('\n')}`;
                        if (data.errores.length > 5) {
                            mensaje += `\n... y ${data.errores.length - 5} error(es) más.`;
                        }
                    }
                    mostrarMensaje('Éxito', mensaje, 'success');
                    // Cerrar el modal de carga
                    const modalFactor = document.getElementById('carga-factor-modal-overlay');
                    const modalMonto = document.getElementById('carga-monto-modal-overlay');
                    if (modalFactor) modalFactor.style.display = 'none';
                    if (modalMonto) modalMonto.style.display = 'none';
                    
                    // Buscar todas las calificaciones sin filtros para mostrarlas
                    setTimeout(() => {
                        // Limpiar filtros del dashboard
                        if (dashboardMercado) dashboardMercado.value = '';
                        if (dashboardOrigen) dashboardOrigen.value = '';
                        if (dashboardPeriodo) dashboardPeriodo.value = '';
                        
                        // Hacer la búsqueda sin filtros (parámetros vacíos)
                        const params = new URLSearchParams();
                        const url = `${buscarCalificacionesUrl}?${params.toString()}`;
                        
                        console.log('Buscando calificaciones después de grabar:', url);
                        
                        fetch(url, {
                            method: 'GET',
                            headers: {
                                'X-CSRFToken': csrftoken
                            }
                        })
                            .then(response => response.json())
                            .then(data => {
                                console.log('Calificaciones recibidas después de grabar:', data);
                                if (data.success) {
                                    renderizarCalificaciones(data.calificaciones);
                                    console.log(`Se cargaron ${data.total} calificación(es) después de grabar`);
                                } else {
                                    console.error('Error al buscar calificaciones:', data.error);
                                }
                            })
                            .catch(error => {
                                console.error('Error al buscar calificaciones:', error);
                            });
                    }, 1500);
                } else {
                    // Si no se grabaron registros, mostrar los errores
                    let mensajeError = 'No se grabaron calificaciones.\n\nErrores encontrados:\n';
                    if (data.errores && data.errores.length > 0) {
                        mensajeError += data.errores.slice(0, 10).join('\n');
                        if (data.errores.length > 10) {
                            mensajeError += `\n... y ${data.errores.length - 10} error(es) más.`;
                        }
                    } else {
                        mensajeError += 'No se encontraron errores específicos.';
                    }
                    mostrarMensaje('Error', mensajeError, 'error');
                }
            } else {
                // Si hay error de duplicado, mostrar mensaje específico
                if (data.duplicado) {
                    mostrarMensaje('Archivo Duplicado', data.error || 'Este archivo ya fue procesado anteriormente', 'error');
                } else {
                    mostrarMensaje('Error', data.error || 'Error al grabar los datos', 'error');
                }
            }
        })
        .catch(error => {
            console.error('Error completo:', error);
            // Si el error tiene un mensaje personalizado, mostrarlo
            if (error.message && error.message.includes('Error del servidor')) {
                mostrarMensaje('Error', error.message, 'error');
            } else {
                mostrarMensaje('Error', 'Error al grabar los datos: ' + error.message, 'error');
            }
        });
    }
    
    // ============================================
    // FUNCIÓN: calcularFactoresDesdeMontos(datos)
    // ============================================
    /**
     * Calcula factores desde montos para múltiples filas de CSV (carga masiva).
     * 
     * POR QUÉ ESTA FUNCIÓN ES CRÍTICA:
     * - Calcula factores para múltiples calificaciones a la vez
     * - Optimiza el proceso de carga masiva
     * - Aplica la misma fórmula que calcular_factores_view pero en lote
     * - Valida que factores no excedan 1.0 (100%)
     * 
     * CÓMO FUNCIONA:
     * 1. Envía todas las filas del CSV al servidor
     * 2. Para cada fila, el servidor:
     *    a. Extrae montos (F8 MONT a F37 MONT)
     *    b. Calcula SumaBase (suma de montos 8-19)
     *    c. Calcula factores: Factor = Monto / SumaBase
     *    d. Valida que factores no excedan 1.0
     * 3. Retorna todas las filas con factores calculados
     * 4. Actualiza la previsualización con factores calculados
     * 
     * FÓRMULA:
     * - SumaBase = suma de montos del 8 al 19
     * - Factor = Monto / SumaBase (para cada monto del 8 al 37)
     * - Factor máximo = 1.0 (si excede, se ajusta a 1.0)
     * 
     * Parámetros:
     *   - datos: Array de objetos con datos del CSV (cada objeto es una fila con montos)
     */
    function calcularFactoresDesdeMontos(datos) {
        const url = window.DJANGO_URLS?.calcularFactoresMasivo || '/prueba/calcular-factores-masivo/';
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ datos: datos })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Actualizar datos con factores calculados
                datosCSVMonto = data.datos_calculados;
                // Mostrar preview actualizado con factores calculados
                mostrarPreviewMontoConFactores(data.datos_calculados);
                if (btnGrabarMonto) btnGrabarMonto.disabled = false;
                mostrarMensaje('Éxito', 'Factores calculados exitosamente', 'success');
            } else {
                mostrarMensaje('Error', data.error || 'Error al calcular los factores', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarMensaje('Error', 'Error al calcular los factores. Por favor, intente nuevamente.', 'error');
        });
    }
    
    // Ver formato - Factor
    if (btnVerFormatoFactor) {
        btnVerFormatoFactor.addEventListener('click', () => {
            mostrarFormatoRequerido('factor');
        });
    }
    
    // Ver formato - Monto
    if (btnVerFormatoMonto) {
        btnVerFormatoMonto.addEventListener('click', () => {
            mostrarFormatoRequerido('monto');
        });
    }
    
    // Función para mostrar formato requerido
    // ============================================
    // FUNCIÓN: mostrarFormatoRequerido(tipo)
    // ============================================
    /**
     * Muestra un modal informativo con el formato requerido para los archivos CSV.
     * 
     * POR QUÉ ESTA FUNCIÓN ES ÚTIL:
     * - Ayuda al usuario a entender qué formato debe tener el CSV
     * - Muestra diferentes formatos según el tipo de carga (factor o monto)
     * - Previene errores al cargar archivos con formato incorrecto
     * 
     * CÓMO FUNCIONA:
     * 1. Determina el mensaje según el tipo (factor o monto)
     * 2. Muestra las columnas requeridas y opcionales
     * 3. Explica qué debe contener cada columna
     * 4. Muestra el mensaje en un modal usando mostrarMensaje()
     * 
     * FORMATOS:
     * - factor: CSV con columnas Ejercicio, Mercado, Instrumento, FEC_PAGO, SEC_EVE, DESCRIPCION, F8-F37 (factores)
     * - monto: CSV con columnas Ejercicio, Mercado, Instrumento, FEC_PAGO, SEC_EVE, DESCRIPCION, F8 MONT-F37 MONT (montos)
     * 
     * Parámetros:
     *   - tipo: Tipo de carga ('factor' o 'monto')
     */
    function mostrarFormatoRequerido(tipo) {
        let mensaje = '';
        if (tipo === 'factor') {
            mensaje = `
                <strong>Formato requerido para Carga Por Factor:</strong><br><br>
                El archivo CSV debe contener las siguientes columnas:<br>
                - Ejercicio (requerido)<br>
                - Mercado (requerido)<br>
                - Instrumento<br>
                - FEC_PAGO<br>
                - SEC_EVE<br>
                - DESCRIPCION<br>
                - F8, F9, F10, ..., F37 (factores del 8 al 37)<br><br>
                Los factores deben estar ya calculados y ser valores decimales entre 0 y 1.
            `;
        } else {
            mensaje = `
                <strong>Formato requerido para Carga Por Monto:</strong><br><br>
                El archivo CSV debe contener las siguientes columnas:<br>
                - Ejercicio (requerido)<br>
                - Mercado (requerido)<br>
                - Instrumento<br>
                - FEC_PAGO<br>
                - SEC_EVE<br>
                - DESCRIPCION<br>
                - F8 MONT, F9 MONT, F10 M, ..., F37 M (montos del 8 al 37)<br><br>
                Los montos serán utilizados para calcular los factores automáticamente.
            `;
        }
        
        mostrarMensaje('Formato Requerido', mensaje, 'info');
    }

    // ========== MODAL DE OPCIONES Y TEMA OSCURO ==========
    const modalOpcionesOverlay = document.getElementById('opciones-modal-overlay');
    const btnAbrirOpciones = document.getElementById('btn-abrir-opciones');
    const btnCerrarOpciones = document.getElementById('btn-cerrar-opciones');
    const btnCerrarOpcionesX = document.getElementById('btn-cerrar-opciones-x');
    const toggleTemaOscuro = document.getElementById('toggle-tema-oscuro');

    // ============================================
    // FUNCIÓN: abrirModalOpciones()
    // ============================================
    /**
     * Abre el modal de opciones del sistema.
     * 
     * POR QUÉ ESTA FUNCIÓN ES NECESARIA:
     * - Permite al usuario acceder a configuraciones del sistema
     * - Muestra opciones como cambio de tema oscuro/claro
     * - Proporciona acceso a funcionalidades adicionales
     * 
     * CÓMO FUNCIONA:
     * 1. Busca el elemento del overlay del modal
     * 2. Cambia su display a 'flex' para mostrarlo
     */
    function abrirModalOpciones() {
        if (modalOpcionesOverlay) {
            modalOpcionesOverlay.style.display = 'flex';
        }
    }

    // ============================================
    // FUNCIÓN: cerrarModalOpciones()
    // ============================================
    /**
     * Cierra el modal de opciones del sistema.
     * 
     * POR QUÉ ESTA FUNCIÓN ES NECESARIA:
     * - Permite cerrar el modal cuando el usuario termina
     * - Oculta el overlay y el contenido del modal
     * 
     * CÓMO FUNCIONA:
     * 1. Busca el elemento del overlay del modal
     * 2. Cambia su display a 'none' para ocultarlo
     */
    function cerrarModalOpciones() {
        if (modalOpcionesOverlay) {
            modalOpcionesOverlay.style.display = 'none';
        }
    }

    // Event listeners para el modal de opciones
    if (btnAbrirOpciones) {
        btnAbrirOpciones.addEventListener('click', abrirModalOpciones);
    }
    if (btnCerrarOpciones) {
        btnCerrarOpciones.addEventListener('click', cerrarModalOpciones);
    }
    if (btnCerrarOpcionesX) {
        btnCerrarOpcionesX.addEventListener('click', cerrarModalOpciones);
    }

    // ========== FUNCIONALIDAD DE TEMA OSCURO ==========
    // ============================================
    // FUNCIÓN: cargarTema()
    // ============================================
    /**
     * Carga y aplica la preferencia de tema (oscuro/claro) guardada en localStorage.
     * 
     * POR QUÉ ESTA FUNCIÓN ES IMPORTANTE:
     * - Mantiene la preferencia del usuario entre sesiones
     * - Aplica el tema inmediatamente al cargar la página
     * - Sincroniza el toggle con la preferencia guardada
     * - Mejora la experiencia de usuario (consistencia)
     * 
     * CÓMO FUNCIONA:
     * 1. Lee la preferencia de tema desde localStorage
     * 2. Si el tema es oscuro, agrega clase 'dark-theme' al body
     * 3. Si el tema es claro, elimina la clase 'dark-theme'
     * 4. Actualiza el estado del toggle para reflejar la preferencia
     * 
     * ALMACENAMIENTO:
     * - localStorage.getItem('temaOscuro'): 'true' para oscuro, 'false' para claro
     * - Se guarda cuando el usuario cambia el toggle
     */
    function cargarTema() {
        // Leer preferencia de tema desde localStorage
        // POR QUÉ: localStorage persiste entre sesiones, mantiene la preferencia del usuario
        // CÓMO: localStorage.getItem() obtiene el valor guardado
        // LÓGICA: Si el valor es 'true', el tema es oscuro. Si es 'false' o null, el tema es claro
        const temaOscuro = localStorage.getItem('temaOscuro') === 'true';
        if (temaOscuro) {
            document.body.classList.add('dark-theme');
            if (toggleTemaOscuro) {
                toggleTemaOscuro.checked = true;
            }
        } else {
            document.body.classList.remove('dark-theme');
            if (toggleTemaOscuro) {
                toggleTemaOscuro.checked = false;
            }
        }
    }

    // Aplicar tema al cargar la página
    cargarTema();

    // Event listener para el toggle de tema oscuro
    if (toggleTemaOscuro) {
        toggleTemaOscuro.addEventListener('change', function() {
            if (this.checked) {
                document.body.classList.add('dark-theme');
                document.documentElement.classList.add('dark-theme');
                localStorage.setItem('temaOscuro', 'true');
            } else {
                document.body.classList.remove('dark-theme');
                document.documentElement.classList.remove('dark-theme');
                localStorage.setItem('temaOscuro', 'false');
            }
            
            // Si el modal de logs está abierto, regenerar el contenido con el nuevo tema
            const modalLogs = document.getElementById('log-calificacion-modal-overlay');
            if (modalLogs && modalLogs.style.display === 'flex' && logsCalificacionActuales && calificacionInfoActual) {
                mostrarLogsCalificacion(logsCalificacionActuales, calificacionInfoActual);
            }
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
});
