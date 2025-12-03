/**
 * DETECTOR DE INACTIVIDAD
 * ========================
 * 
 * POR QUÉ ESTE SCRIPT ES IMPORTANTE:
 * - Protege la seguridad de las sesiones de usuario
 * - Cierra sesiones automáticamente después de períodos de inactividad
 * - Previene que usuarios no autorizados accedan a sesiones abandonadas
 * - Cumple con mejores prácticas de seguridad en aplicaciones web
 * - Muestra advertencia al usuario antes de cerrar la sesión
 * 
 * CÓMO FUNCIONA EL SISTEMA:
 * 1. Detecta actividad del usuario (clics, movimientos, teclas, scroll)
 * 2. Reinicia un temporizador cada vez que detecta actividad
 * 3. Si pasan 5 minutos sin actividad, muestra un modal de advertencia
 * 4. Inicia cuenta regresiva de 10 segundos
 * 5. Si el usuario no responde, cierra la sesión automáticamente
 * 6. Si el usuario presiona "Continuar Sesión", reinicia el temporizador
 * 
 * Configuración:
 * - INACTIVIDAD_TIMEOUT: Tiempo en milisegundos antes de mostrar el modal (5 minutos = 300000 ms)
 * - CUENTA_REGRESIVA: Tiempo en segundos para la cuenta regresiva (10 segundos)
 * - LOGOUT_URL: URL para cerrar sesión
 */

// FUNCIÓN ANÓNIMA AUTO-EJECUTABLE (IIFE - Immediately Invoked Function Expression)
// POR QUÉ: Encapsula todo el código para evitar conflictos con otras variables globales
// CÓMO: Se ejecuta inmediatamente al cargar el script, creando un scope privado
(function() {
    // 'use strict' activa el modo estricto de JavaScript
    // POR QUÉ: Previene errores comunes, hace el código más seguro y optimizable
    // CÓMO: El navegador aplica reglas más estrictas (no permite variables sin declarar, etc.)
    'use strict';

    // ============================================
    // CONFIGURACIÓN
    // ============================================
    
    // Tiempo de inactividad antes de mostrar el modal (en milisegundos)
    // 300000 ms = 5 minutos × 60 segundos × 1000 milisegundos
    // POR QUÉ: 5 minutos es un balance entre seguridad y usabilidad
    // CÓMO: setTimeout() usa milisegundos, por eso convertimos minutos a milisegundos
    const INACTIVIDAD_TIMEOUT = 300000;
    
    // Tiempo de cuenta regresiva antes de cerrar sesión (en segundos)
    // POR QUÉ: 10 segundos da tiempo suficiente para que el usuario reaccione
    // CÓMO: Se usa en la función de cuenta regresiva que se ejecuta cada segundo
    const CUENTA_REGRESIVA = 10;
    
    // URL para cerrar sesión
    // POR QUÉ: Cuando la cuenta regresiva llega a 0, redirige a esta URL
    // CÓMO: window.location.href cambia la página actual a esta URL
    const LOGOUT_URL = '/prueba/logout/';

    // ============================================
    // VARIABLES GLOBALES
    // ============================================
    
    // Referencia al temporizador de inactividad
    // POR QUÉ: Necesitamos guardar la referencia para poder cancelarlo cuando hay actividad
    // CÓMO: setTimeout() retorna un ID que podemos usar con clearTimeout()
    let timeoutInactividad = null;
    
    // Referencia al temporizador de cuenta regresiva
    // POR QUÉ: Necesitamos poder cancelar la cuenta regresiva si el usuario presiona el botón
    // CÓMO: setTimeout() retorna un ID que podemos usar con clearTimeout()
    let timeoutCuentaRegresiva = null;
    
    // Contador de segundos restantes en la cuenta regresiva
    // POR QUÉ: Necesitamos saber cuántos segundos quedan para mostrar al usuario
    // CÓMO: Se decrementa cada segundo en la función actualizarCuenta()
    let cuentaRegresivaRestante = CUENTA_REGRESIVA;
    
    // Flag que indica si el modal de inactividad está visible
    // POR QUÉ: Evita mostrar múltiples modales y controla el comportamiento del temporizador
    // CÓMO: Se establece en true cuando se muestra el modal, false cuando se cierra
    let modalVisible = false;
    
    // Flag que indica si el usuario está activo
    // POR QUÉ: Controla si debemos reiniciar el temporizador cuando la página se vuelve visible
    // CÓMO: Se establece en false cuando se muestra el modal, true cuando hay actividad
    let esActivo = true;

    // ============================================
    // FUNCIONES DE DETECCIÓN DE ACTIVIDAD
    // ============================================
    
    /**
     * Reinicia el temporizador de inactividad cuando detecta actividad del usuario.
     * 
     * POR QUÉ ESTA FUNCIÓN ES CRÍTICA:
     * - Es el corazón del sistema de detección de inactividad
     * - Se llama cada vez que el usuario hace algo (clic, movimiento, tecla, etc.)
     * - Reinicia el contador de 5 minutos cada vez que hay actividad
     * - NO cierra el modal si está visible (el modal solo se cierra con el botón)
     * 
     * CÓMO FUNCIONA:
     * 1. Verifica si el modal está visible (si está visible, no hace nada)
     * 2. Cancela el temporizador anterior (si existe)
     * 3. Marca al usuario como activo
     * 4. Establece un nuevo temporizador de 5 minutos
     * 
     * FLUJO:
     * - Usuario hace clic → reiniciarTemporizador() → cancela temporizador anterior → crea nuevo temporizador
     * - Si pasan 5 minutos sin actividad → mostrarModalInactividad()
     */
    function reiniciarTemporizador() {
        // Verificar si el modal de inactividad está visible
        // POR QUÉ: Si el modal está visible, NO queremos reiniciar el temporizador
        // CÓMO: El modal solo se cierra cuando el usuario presiona el botón explícitamente
        // LÓGICA: Si el usuario está viendo el modal, no queremos que su actividad lo cierre automáticamente
        if (modalVisible) {
            // Retornar sin hacer nada
            // POR QUÉ: El modal debe cerrarse solo con el botón "Continuar Sesión"
            // CÓMO: return sale de la función inmediatamente sin ejecutar el resto del código
            return;
        }

        // Limpiar el temporizador anterior si existe
        // POR QUÉ: Si no lo cancelamos, tendríamos múltiples temporizadores corriendo simultáneamente
        // CÓMO: clearTimeout() cancela el temporizador usando su ID
        // LÓGICA: Cada vez que hay actividad, cancelamos el temporizador anterior y creamos uno nuevo
        if (timeoutInactividad) {
            // clearTimeout() cancela el temporizador identificado por timeoutInactividad
            // POR QUÉ: Evita que se ejecuten múltiples temporizadores al mismo tiempo
            clearTimeout(timeoutInactividad);
        }

        // Marcar al usuario como activo
        // POR QUÉ: Esta variable controla si debemos reiniciar el temporizador cuando la página se vuelve visible
        // CÓMO: Se establece en true cuando hay actividad, false cuando se muestra el modal
        esActivo = true;

        // Establecer nuevo temporizador de inactividad
        // POR QUÉ: Después de cada actividad, reiniciamos el contador de 5 minutos
        // CÓMO: setTimeout() programa una función para ejecutarse después de X milisegundos
        // LÓGICA: Si pasan 5 minutos (300000 ms) sin más actividad, se ejecutará mostrarModalInactividad()
        // Guardamos el ID del temporizador en timeoutInactividad para poder cancelarlo después
        timeoutInactividad = setTimeout(mostrarModalInactividad, INACTIVIDAD_TIMEOUT);
    }

    /**
     * Crea y muestra el modal de inactividad con cuenta regresiva.
     * 
     * POR QUÉ ESTA FUNCIÓN ES IMPORTANTE:
     * - Muestra advertencia al usuario antes de cerrar la sesión
     * - Da oportunidad al usuario de mantener su sesión activa
     * - Inicia la cuenta regresiva visual para crear urgencia
     * 
     * CÓMO FUNCIONA:
     * 1. Verifica que el modal no esté ya visible (evita duplicados)
     * 2. Marca el modal como visible y al usuario como inactivo
     * 3. Crea el modal si no existe (solo la primera vez)
     * 4. Muestra el modal en pantalla
     * 5. Resetea el contador visual a color amarillo
     * 6. Inicia la cuenta regresiva
     */
    function mostrarModalInactividad() {
        // Verificar si el modal ya está visible
        // POR QUÉ: Evita mostrar múltiples modales si la función se llama varias veces
        // CÓMO: Si modalVisible es true, significa que el modal ya está mostrándose
        // LÓGICA: Solo mostramos el modal si no está ya visible
        if (modalVisible) {
            // Retornar sin hacer nada
            // POR QUÉ: No queremos crear múltiples modales
            return;
        }

        // Marcar el modal como visible
        // POR QUÉ: Esta variable controla si el modal está mostrándose
        // CÓMO: Se establece en true cuando se muestra, false cuando se cierra
        modalVisible = true;
        
        // Marcar al usuario como inactivo
        // POR QUÉ: Controla si debemos reiniciar el temporizador cuando la página se vuelve visible
        // CÓMO: Se establece en false cuando se muestra el modal
        esActivo = false;
        
        // Resetear el contador de cuenta regresiva al valor inicial
        // POR QUÉ: Cada vez que se muestra el modal, la cuenta regresiva debe empezar desde 10
        // CÓMO: Asignamos el valor constante CUENTA_REGRESIVA (10 segundos)
        cuentaRegresivaRestante = CUENTA_REGRESIVA;

        // Crear el modal si no existe en el DOM
        // POR QUÉ: El modal solo se crea una vez, la primera vez que se necesita
        // CÓMO: Verificamos si existe un elemento con id 'modal-inactividad-overlay'
        // LÓGICA: Si no existe, lo creamos. Si ya existe, solo lo mostramos
        if (!document.getElementById('modal-inactividad-overlay')) {
            // Llamar a la función que crea el HTML del modal
            // POR QUÉ: Esta función crea todos los elementos HTML del modal
            crearModalInactividad();
        }

        // Obtener referencias a los elementos del modal
        // POR QUÉ: Necesitamos estos elementos para mostrarlos
        // CÓMO: getElementById() busca un elemento en el DOM por su ID
        const overlay = document.getElementById('modal-inactividad-overlay');
        const modal = document.getElementById('modal-inactividad');
        
        // Verificar que los elementos existan antes de intentar mostrarlos
        // POR QUÉ: Si los elementos no existen, no podemos mostrarlos y causaríamos un error
        // CÓMO: Si overlay o modal son null, significa que no se encontraron en el DOM
        // LÓGICA: Si no existen, mostramos error en consola y salimos de la función
        if (!overlay || !modal) {
            // console.error() muestra un mensaje de error en la consola del navegador
            // POR QUÉ: Ayuda a diagnosticar problemas durante desarrollo
            console.error('Error: No se pudo encontrar el overlay o el modal de inactividad');
            // Retornar sin hacer nada
            // POR QUÉ: No podemos continuar si los elementos no existen
            return;
        }
        
        // Mostrar el overlay (fondo oscuro)
        // POR QUÉ: El overlay es el fondo semitransparente que cubre toda la pantalla
        // CÓMO: display: 'flex' hace que el elemento sea visible y use flexbox para centrar el modal
        overlay.style.display = 'flex';
        
        // Mostrar el modal (contenido)
        // POR QUÉ: El modal es el cuadro de diálogo que contiene el mensaje y el botón
        // CÓMO: display: 'block' hace que el elemento sea visible
        modal.style.display = 'block';
        
        // Asegurar que el overlay tenga un z-index alto
        // POR QUÉ: El modal debe aparecer por encima de todos los demás elementos de la página
        // CÓMO: z-index controla el orden de apilamiento de elementos (mayor = más arriba)
        // LÓGICA: 10003 es un valor alto que asegura que esté por encima de otros modales (10000, 10001, etc.)
        overlay.style.zIndex = '10003';

        // Resetear el contador visual a su estado inicial
        // POR QUÉ: Cada vez que se muestra el modal, el contador debe empezar en amarillo
        // CÓMO: Obtenemos el elemento del contador y restablecemos su estilo
        const contador = document.getElementById('contador-inactividad');
        if (contador) {
            // Establecer color inicial a amarillo (advertencia)
            // POR QUÉ: El amarillo indica advertencia, no peligro inmediato
            // CÓMO: var(--color-warning) es una variable CSS que contiene el color amarillo
            contador.style.color = 'var(--color-warning)';
            
            // Quitar cualquier animación previa
            // POR QUÉ: Si había una animación de pulso anterior, la eliminamos
            // CÓMO: animation: 'none' desactiva todas las animaciones CSS
            contador.style.animation = 'none';
            
            // Forzar reflow del navegador para resetear la animación
            // POR QUÉ: A veces el navegador cachea estilos, necesitamos forzar una actualización
            // CÓMO: Acceder a offsetWidth fuerza al navegador a recalcular el layout
            // LÓGICA: void indica que ignoramos el valor de retorno, solo queremos el efecto secundario
            void contador.offsetWidth;
        }

        // Iniciar la cuenta regresiva
        // POR QUÉ: Después de mostrar el modal, debemos empezar a contar hacia atrás
        // CÓMO: Esta función actualiza el contador cada segundo
        iniciarCuentaRegresiva();
    }

    /**
     * Cierra el modal de inactividad y reinicia el temporizador.
     * 
     * POR QUÉ ESTA FUNCIÓN ES NECESARIA:
     * - Permite al usuario mantener su sesión activa
     * - Cancela la cuenta regresiva cuando el usuario responde
     * - Reinicia el temporizador de inactividad para dar otros 5 minutos
     * 
     * CÓMO FUNCIONA:
     * 1. Verifica que el modal esté visible (evita errores)
     * 2. Marca el modal como no visible y al usuario como activo
     * 3. Cancela la cuenta regresiva
     * 4. Oculta el modal y el overlay
     * 5. Reinicia el temporizador de inactividad
     */
    function cerrarModalInactividad() {
        // Verificar que el modal esté visible antes de intentar cerrarlo
        // POR QUÉ: Evita ejecutar código innecesario si el modal ya está cerrado
        // CÓMO: Si modalVisible es false, el modal no está visible
        if (!modalVisible) {
            // Retornar sin hacer nada
            // POR QUÉ: No hay nada que cerrar
            return;
        }

        // Marcar el modal como no visible
        // POR QUÉ: Indica que el modal ya no está mostrándose
        // CÓMO: Se establece en false
        modalVisible = false;
        
        // Marcar al usuario como activo
        // POR QUÉ: El usuario respondió, por lo tanto está activo
        // CÓMO: Se establece en true
        esActivo = true;

        // Cancelar la cuenta regresiva si está corriendo
        // POR QUÉ: Si el usuario presiona el botón, no queremos que la cuenta regresiva continúe
        // CÓMO: clearTimeout() cancela el temporizador usando su ID
        if (timeoutCuentaRegresiva) {
            // Cancelar el temporizador de cuenta regresiva
            // POR QUÉ: Evita que la cuenta regresiva continúe después de cerrar el modal
            clearTimeout(timeoutCuentaRegresiva);
            // Establecer en null para indicar que no hay temporizador activo
            // POR QUÉ: Limpia la referencia para evitar usar un ID inválido
            timeoutCuentaRegresiva = null;
        }

        // Obtener referencias a los elementos del modal
        // POR QUÉ: Necesitamos estos elementos para ocultarlos
        const overlay = document.getElementById('modal-inactividad-overlay');
        const modal = document.getElementById('modal-inactividad');
        
        // Ocultar el overlay si existe
        // POR QUÉ: El overlay es el fondo oscuro, debe ocultarse junto con el modal
        // CÓMO: display: 'none' hace que el elemento sea invisible
        if (overlay) {
            overlay.style.display = 'none';
        }
        
        // Ocultar el modal si existe
        // POR QUÉ: El modal debe desaparecer de la pantalla
        // CÓMO: display: 'none' hace que el elemento sea invisible
        if (modal) {
            modal.style.display = 'none';
        }

        // Reiniciar el temporizador de inactividad
        // POR QUÉ: El usuario respondió, así que le damos otros 5 minutos de inactividad
        // CÓMO: Esta función cancela el temporizador anterior y crea uno nuevo
        reiniciarTemporizador();
    }

    /**
     * Crea el HTML del modal de inactividad.
     * 
     * POR QUÉ ESTA FUNCIÓN ES NECESARIA:
     * - Crea dinámicamente el HTML del modal la primera vez que se necesita
     * - No requiere que el HTML esté en el template (más flexible)
     * - Configura todos los event listeners necesarios
     * 
     * CÓMO FUNCIONA:
     * 1. Crea el elemento overlay (fondo oscuro)
     * 2. Crea el elemento modal (contenido)
     * 3. Agrega el HTML interno del modal con template strings
     * 4. Agrega el modal al overlay y el overlay al body
     * 5. Configura el event listener del botón "Continuar Sesión"
     * 6. Previene que el modal se cierre al hacer clic fuera de él
     */
    function crearModalInactividad() {
        // Crear el elemento overlay (fondo oscuro semitransparente)
        // POR QUÉ: El overlay cubre toda la pantalla y crea el efecto de modal
        // CÓMO: createElement() crea un nuevo elemento HTML div
        const overlay = document.createElement('div');
        
        // Asignar ID único al overlay
        // POR QUÉ: Necesitamos poder encontrarlo después con getElementById()
        // CÓMO: id es un atributo HTML que identifica de forma única un elemento
        overlay.id = 'modal-inactividad-overlay';
        
        // Asignar clases CSS al overlay
        // POR QUÉ: Las clases CSS proporcionan los estilos (posición, color, etc.)
        // CÓMO: className asigna múltiples clases separadas por espacios
        // LÓGICA: 'modal-overlay' es la clase base, 'modal-inactividad-overlay' es específica para este modal
        overlay.className = 'modal-overlay modal-inactividad-overlay';
        
        // Crear el elemento modal (contenido del diálogo)
        // POR QUÉ: El modal es el cuadro de diálogo que contiene el mensaje
        // CÓMO: createElement() crea un nuevo elemento HTML div
        const modal = document.createElement('div');
        
        // Asignar ID único al modal
        // POR QUÉ: Necesitamos poder encontrarlo después con getElementById()
        modal.id = 'modal-inactividad';
        
        // Asignar clases CSS al modal
        // POR QUÉ: Las clases CSS proporcionan los estilos (tamaño, posición, etc.)
        // CÓMO: 'modal-content' es la clase base, 'modal-small' hace el modal más pequeño
        modal.className = 'modal-content modal-small';
        
        // Agregar el HTML interno del modal usando template strings
        // POR QUÉ: Template strings permiten insertar variables (${CUENTA_REGRESIVA}) en el HTML
        // CÓMO: innerHTML establece el contenido HTML del elemento
        // LÓGICA: Creamos la estructura completa del modal: header, body con mensaje y contador, footer con botón
        modal.innerHTML = `
            <div class="modal-header">
                <h2><i class="bi bi-exclamation-triangle-fill" style="margin-right: 0.5rem;"></i>Sesión por expirar</h2>
            </div>
            <div class="modal-body">
                <div style="text-align: center; padding: 1rem;">
                    <p style="font-size: 1.1rem; margin-bottom: 1rem; color: var(--text-primary);">
                        Has estado inactivo por un período prolongado.
                    </p>
                    <p style="font-size: 1rem; margin-bottom: 1.5rem; color: var(--text-secondary);">
                        Tu sesión se cerrará automáticamente en:
                    </p>
                    <div id="contador-inactividad" style="font-size: 3rem; font-weight: bold; color: var(--color-warning); margin: 1rem 0;">
                        ${CUENTA_REGRESIVA}
                    </div>
                    <p style="font-size: 0.9rem; color: var(--text-secondary); font-style: italic;">
                        Presiona el botón "Continuar Sesión" para mantener tu sesión activa.
                    </p>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" id="btn-continuar-sesion" class="btn">
                    Continuar Sesión
                </button>
            </div>
        `;
        
        // Agregar el modal dentro del overlay
        // POR QUÉ: El overlay contiene el modal, así el overlay cubre toda la pantalla
        // CÓMO: appendChild() agrega un elemento como hijo de otro
        overlay.appendChild(modal);
        
        // Agregar el overlay al body del documento
        // POR QUÉ: El overlay debe estar en el body para cubrir toda la página
        // CÓMO: appendChild() agrega el overlay como último hijo del body
        document.body.appendChild(overlay);

        // Configurar el event listener del botón "Continuar Sesión"
        // POR QUÉ: Este es el ÚNICO botón que puede cerrar el modal
        // CÓMO: Buscamos el botón por su ID y agregamos un listener de clic
        const btnContinuar = document.getElementById('btn-continuar-sesion');
        if (btnContinuar) {
            // Agregar event listener para el evento 'click'
            // POR QUÉ: Cuando el usuario hace clic en el botón, queremos cerrar el modal
            // CÓMO: addEventListener() registra una función que se ejecuta cuando ocurre el evento
            // LÓGICA: cerrarModalInactividad() se ejecutará cuando se haga clic en el botón
            btnContinuar.addEventListener('click', cerrarModalInactividad);
        }

        // Prevenir que el modal se cierre al hacer clic en el overlay
        // POR QUÉ: El modal solo debe cerrarse con el botón explícito, no accidentalmente
        // CÓMO: Agregamos un listener al overlay que previene el comportamiento por defecto
        overlay.addEventListener('click', function(e) {
            // Verificar si el clic fue directamente en el overlay (no en el modal)
            // POR QUÉ: Si el clic fue en el overlay (fondo), no queremos hacer nada
            // CÓMO: e.target es el elemento donde ocurrió el clic, overlay es el elemento del overlay
            // LÓGICA: Si e.target === overlay, el clic fue en el fondo, no en el modal
            if (e.target === overlay) {
                // Detener la propagación del evento
                // POR QUÉ: Evita que el evento se propague a otros elementos
                // CÓMO: stopPropagation() detiene el bubbling del evento
                e.stopPropagation();
                
                // Prevenir el comportamiento por defecto
                // POR QUÉ: Algunos navegadores pueden tener comportamientos por defecto en clics
                // CÓMO: preventDefault() cancela el comportamiento por defecto del evento
                e.preventDefault();
            }
        });
        
        // Prevenir que se cierre el modal al hacer clic en el contenido del modal
        // POR QUÉ: Cualquier clic dentro del modal no debe cerrarlo
        // CÓMO: Agregamos un listener al modal que detiene la propagación del evento
        modal.addEventListener('click', function(e) {
            // Detener la propagación del evento
            // POR QUÉ: Evita que el clic se propague al overlay y cause que se cierre
            // CÓMO: stopPropagation() detiene el bubbling del evento
            e.stopPropagation();
        });
    }

    /**
     * Inicia la cuenta regresiva y actualiza el contador cada segundo.
     * 
     * POR QUÉ ESTA FUNCIÓN ES CRÍTICA:
     * - Muestra visualmente cuánto tiempo queda antes de cerrar la sesión
     * - Crea urgencia para que el usuario responda
     * - Cambia el color del contador cuando quedan pocos segundos (rojo + animación)
     * - Cierra la sesión automáticamente cuando llega a 0
     * 
     * CÓMO FUNCIONA:
     * 1. Obtiene el elemento del contador del DOM
     * 2. Establece el valor inicial y color amarillo
     * 3. Crea una función recursiva que se ejecuta cada segundo
     * 4. Decrementa el contador y actualiza el DOM
     * 5. Cambia a rojo cuando quedan 3 segundos o menos
     * 6. Redirige a logout cuando llega a 0
     */
    function iniciarCuentaRegresiva() {
        // Obtener el elemento del contador del DOM
        // POR QUÉ: Necesitamos actualizar el número que se muestra al usuario
        // CÓMO: getElementById() busca el elemento con id 'contador-inactividad'
        const contador = document.getElementById('contador-inactividad');
        
        // Actualizar el contador inmediatamente con el valor inicial
        // POR QUÉ: El usuario debe ver el contador desde el primer momento
        // CÓMO: Verificamos que el elemento exista antes de modificarlo
        if (contador) {
            // Establecer el texto del contador al valor inicial
            // POR QUÉ: Muestra cuántos segundos quedan (empieza en 10)
            // CÓMO: textContent establece el texto visible del elemento
            contador.textContent = cuentaRegresivaRestante;
            
            // Establecer color inicial a amarillo si el contador es mayor a 3
            // POR QUÉ: El amarillo indica advertencia, no peligro inmediato
            // CÓMO: Si quedan más de 3 segundos, usamos color de advertencia (amarillo)
            if (cuentaRegresivaRestante > 3) {
                // Establecer color a amarillo (advertencia)
                // POR QUÉ: Indica que hay tiempo pero debe actuar pronto
                // CÓMO: var(--color-warning) es una variable CSS con el color amarillo
                contador.style.color = 'var(--color-warning)';
                
                // Desactivar animación
                // POR QUÉ: La animación solo se activa cuando quedan 3 segundos o menos
                // CÓMO: animation: 'none' desactiva todas las animaciones CSS
                contador.style.animation = 'none';
            }
        }

        // Función recursiva que se ejecuta cada segundo
        // POR QUÉ: Necesitamos actualizar el contador cada segundo hasta llegar a 0
        // CÓMO: Esta función se llama a sí misma usando setTimeout() cada 1000 ms (1 segundo)
        // LÓGICA: Es recursiva porque se programa a sí misma para ejecutarse de nuevo
        function actualizarCuenta() {
            // Decrementar el contador en 1
            // POR QUÉ: Cada segundo, el tiempo restante disminuye
            // CÓMO: -- es el operador de decremento (resta 1)
            cuentaRegresivaRestante--;

            // Actualizar el contador en el DOM
            // POR QUÉ: El usuario debe ver el número actualizado
            // CÓMO: Verificamos que el elemento exista antes de modificarlo
            if (contador) {
                // Establecer el texto del contador al nuevo valor
                // POR QUÉ: Muestra el número de segundos restantes actualizado
                // CÓMO: textContent actualiza el texto visible del elemento
                contador.textContent = cuentaRegresivaRestante;
                
                // Cambiar color y animación cuando quedan 3 segundos o menos
                // POR QUÉ: El rojo y la animación crean urgencia visual
                // CÓMO: Si el contador es <= 3, cambiamos a color de peligro (rojo)
                if (cuentaRegresivaRestante <= 3) {
                    // Establecer color a rojo (peligro)
                    // POR QUÉ: El rojo indica peligro inmediato, tiempo casi agotado
                    // CÓMO: var(--color-danger) es una variable CSS con el color rojo
                    contador.style.color = 'var(--color-danger)';
                    
                    // Activar animación de pulso
                    // POR QUÉ: La animación llama la atención del usuario
                    // CÓMO: 'pulse 0.5s infinite' es una animación CSS que hace el elemento pulsar
                    // LÓGICA: 0.5s es la duración de cada pulso, infinite hace que se repita indefinidamente
                    contador.style.animation = 'pulse 0.5s infinite';
                } else {
                    // Mantener color amarillo si es mayor a 3
                    // POR QUÉ: Mientras hay tiempo suficiente, mantenemos el color de advertencia
                    // CÓMO: var(--color-warning) es el color amarillo
                    contador.style.color = 'var(--color-warning)';
                    
                    // Desactivar animación
                    // POR QUÉ: La animación solo se activa cuando hay urgencia (≤3 segundos)
                    // CÓMO: animation: 'none' desactiva todas las animaciones
                    contador.style.animation = 'none';
                }
            }

            // Verificar si la cuenta regresiva llegó a 0
            // POR QUÉ: Cuando llega a 0, debemos cerrar la sesión automáticamente
            // CÓMO: Si cuentaRegresivaRestante es <= 0, redirigimos a logout
            if (cuentaRegresivaRestante <= 0) {
                // Redirigir a la URL de logout
                // POR QUÉ: El tiempo se agotó, debemos cerrar la sesión
                // CÓMO: window.location.href cambia la página actual a la URL especificada
                // LÓGICA: Al cambiar la URL, el navegador carga la página de logout, que cierra la sesión
                window.location.href = LOGOUT_URL;
                
                // Retornar para detener la ejecución
                // POR QUÉ: No queremos continuar la cuenta regresiva después de redirigir
                // CÓMO: return sale de la función inmediatamente
                return;
            }

            // Continuar la cuenta regresiva si el modal sigue visible
            // POR QUÉ: Si el modal fue cerrado, no debemos continuar contando
            // CÓMO: Verificamos que modalVisible sea true antes de programar el siguiente segundo
            // LÓGICA: Si el usuario cerró el modal, modalVisible será false y no continuaremos
            if (modalVisible) {
                // Programar la siguiente actualización después de 1 segundo (1000 ms)
                // POR QUÉ: Queremos actualizar el contador cada segundo
                // CÓMO: setTimeout() programa la función actualizarCuenta() para ejecutarse después de 1000 ms
                // LÓGICA: Guardamos el ID del temporizador para poder cancelarlo si es necesario
                timeoutCuentaRegresiva = setTimeout(actualizarCuenta, 1000);
            }
        }

        // Iniciar la cuenta regresiva después de 1 segundo
        // POR QUÉ: Queremos que el contador se actualice por primera vez después de 1 segundo
        // CÓMO: setTimeout() programa la función actualizarCuenta() para ejecutarse después de 1000 ms
        // LÓGICA: Esto crea el efecto de que el contador se actualiza cada segundo
        timeoutCuentaRegresiva = setTimeout(actualizarCuenta, 1000);
    }

    // ============================================
    // EVENTOS DE ACTIVIDAD DEL USUARIO
    // ============================================
    
    // Lista de eventos que indican actividad del usuario
    // POR QUÉ: Estos eventos indican que el usuario está interactuando con la página
    // CÓMO: Cada evento se detecta y reinicia el temporizador de inactividad
    // LÓGICA: Si el usuario hace cualquiera de estas acciones, está activo
    const eventosActividad = [
        'mousedown',    // Presionar botón del mouse (clic, pero antes de soltar)
        'mousemove',    // Mover el mouse sobre la página
        'keypress',     // Presionar una tecla del teclado
        'scroll',       // Hacer scroll en la página
        'touchstart',   // Tocar la pantalla (dispositivos táctiles)
        'click'         // Hacer clic en cualquier elemento
    ];

    // Agregar event listeners para cada evento de actividad
    // POR QUÉ: Necesitamos detectar cuando el usuario hace cualquiera de estas acciones
    // CÓMO: forEach() itera sobre cada evento y agrega un listener
    // LÓGICA: Cada vez que ocurre cualquiera de estos eventos, se ejecuta reiniciarTemporizador()
    eventosActividad.forEach(function(evento) {
        // Agregar event listener al documento para este evento
        // POR QUÉ: Queremos detectar el evento en cualquier parte de la página
        // CÓMO: addEventListener() registra una función que se ejecuta cuando ocurre el evento
        // LÓGICA: 'true' como tercer parámetro significa "capture phase" (detecta el evento antes de que llegue al elemento)
        // POR QUÉ USAR CAPTURE: Asegura que detectamos el evento incluso si otro código lo detiene
        document.addEventListener(evento, reiniciarTemporizador, true);
    });

    // También detectar actividad cuando la ventana recibe el foco
    // POR QUÉ: Si el usuario cambia de pestaña y vuelve, eso también es actividad
    // CÓMO: El evento 'focus' se dispara cuando la ventana del navegador recibe el foco
    // LÓGICA: Si el usuario vuelve a la pestaña, reiniciamos el temporizador
    window.addEventListener('focus', reiniciarTemporizador);

    // ============================================
    // INICIALIZACIÓN
    // ============================================
    
    /**
     * Inicializa el detector de inactividad cuando el DOM está listo.
     * 
     * POR QUÉ ESTA FUNCIÓN ES NECESARIA:
     * - Asegura que el sistema solo se active en páginas que no sean login
     * - Espera a que el DOM esté completamente cargado
     * - Inicia el temporizador de inactividad por primera vez
     * 
     * CÓMO FUNCIONA:
     * 1. Verifica si estamos en la página de login (no activar en login)
     * 2. Verifica el estado del DOM (loading o listo)
     * 3. Inicia el temporizador de inactividad
     */
    function inicializar() {
        // Obtener la ruta actual de la página
        // POR QUÉ: Necesitamos saber en qué página estamos para decidir si activar el detector
        // CÓMO: window.location.pathname contiene la ruta de la URL actual
        const rutaActual = window.location.pathname;
        
        // Verificar si estamos en la página de login
        // POR QUÉ: No queremos activar el detector de inactividad en la página de login
        // CÓMO: Verificamos si la ruta contiene '/login/' o es la ruta raíz
        // LÓGICA: Si es login, no activamos el detector (el usuario aún no tiene sesión)
        const esLogin = rutaActual.includes('/login/') || 
                       rutaActual === '/' || 
                       rutaActual === '/prueba/' ||
                       rutaActual.endsWith('/login');
        
        // Si estamos en login, no inicializar el detector
        // POR QUÉ: En login no hay sesión que proteger, no tiene sentido detectar inactividad
        // CÓMO: return sale de la función sin hacer nada
        if (esLogin) {
            return;
        }

        // Verificar el estado del DOM
        // POR QUÉ: Necesitamos asegurarnos de que el DOM esté listo antes de iniciar
        // CÓMO: document.readyState puede ser 'loading', 'interactive', o 'complete'
        // LÓGICA: Si está 'loading', esperamos. Si ya está listo, iniciamos inmediatamente
        if (document.readyState === 'loading') {
            // El DOM aún se está cargando, esperar a que esté listo
            // POR QUÉ: No podemos iniciar el detector antes de que el DOM esté completamente cargado
            // CÓMO: DOMContentLoaded se dispara cuando el HTML está completamente cargado y parseado
            // LÓGICA: Cuando el DOM esté listo, ejecutamos reiniciarTemporizador()
            document.addEventListener('DOMContentLoaded', function() {
                // Iniciar el temporizador de inactividad
                // POR QUÉ: Ahora que el DOM está listo, podemos empezar a detectar inactividad
                // CÓMO: Esta función establece el primer temporizador de 5 minutos
                reiniciarTemporizador();
            });
        } else {
            // El DOM ya está listo, iniciar inmediatamente
            // POR QUÉ: Si el DOM ya está cargado, no necesitamos esperar
            // CÓMO: Llamamos directamente a reiniciarTemporizador()
            reiniciarTemporizador();
        }
    }

    // Inicializar cuando el DOM esté listo
    // POR QUÉ: Queremos que el detector se active tan pronto como sea posible
    // CÓMO: Verificamos el estado del DOM y ejecutamos inicializar() cuando corresponda
    if (document.readyState === 'loading') {
        // El DOM aún se está cargando, esperar al evento DOMContentLoaded
        // POR QUÉ: No podemos inicializar antes de que el DOM esté listo
        // CÓMO: Agregamos un listener para el evento DOMContentLoaded
        document.addEventListener('DOMContentLoaded', inicializar);
    } else {
        // El DOM ya está listo, inicializar inmediatamente
        // POR QUÉ: No hay necesidad de esperar
        // CÓMO: Llamamos directamente a inicializar()
        inicializar();
    }

    // También inicializar después de que todos los recursos se hayan cargado
    // POR QUÉ: Asegura que funcione incluso si el script se carga de forma asíncrona
    // CÓMO: El evento 'load' se dispara cuando todos los recursos (imágenes, CSS, etc.) están cargados
    // LÓGICA: Esto es un respaldo por si el script se carga después de DOMContentLoaded
    if (window.addEventListener) {
        // Agregar listener para el evento 'load'
        // POR QUÉ: Queremos asegurarnos de que el detector se inicialice incluso en casos edge
        // CÓMO: addEventListener() registra una función que se ejecuta cuando todos los recursos están cargados
        window.addEventListener('load', function() {
            // Re-inicializar solo si no se ha iniciado ya
            // POR QUÉ: Evitamos inicializar múltiples veces
            // CÓMO: Verificamos si timeoutInactividad es null (no hay temporizador activo)
            // LÓGICA: Si no hay temporizador, significa que aún no se inicializó, así que lo hacemos
            if (!timeoutInactividad) {
                // Llamar a inicializar() para asegurar que el detector se active
                // POR QUÉ: Si por alguna razón no se inicializó antes, lo hacemos ahora
                inicializar();
            }
        });
    }

    // Reiniciar el temporizador cuando la página se vuelve visible
    // POR QUÉ: Si el usuario cambia de pestaña y vuelve, eso indica actividad
    // CÓMO: El evento 'visibilitychange' se dispara cuando la visibilidad de la página cambia
    // LÓGICA: Si la página se vuelve visible (!document.hidden) y el usuario está activo, reiniciamos
    document.addEventListener('visibilitychange', function() {
        // Verificar que la página se volvió visible y el usuario está activo
        // POR QUÉ: Solo reiniciamos si la página es visible y el usuario no está en el modal de inactividad
        // CÓMO: !document.hidden significa que la página es visible, esActivo significa que no está en modal
        // LÓGICA: Si ambas condiciones son true, el usuario volvió a la pestaña y está activo
        if (!document.hidden && esActivo) {
            // Reiniciar el temporizador de inactividad
            // POR QUÉ: El usuario volvió a la pestaña, así que le damos otros 5 minutos
            // CÓMO: Esta función cancela el temporizador anterior y crea uno nuevo
            reiniciarTemporizador();
        }
    });

// Cerrar la función anónima auto-ejecutable
// POR QUÉ: Esto cierra el scope privado y ejecuta la función inmediatamente
})();
