/**
 * DETECTOR DE INACTIVIDAD
 * ========================
 * Detecta cuando el usuario está inactivo por un período de tiempo y muestra
 * un modal con cuenta regresiva antes de cerrar la sesión automáticamente.
 * 
 * Configuración:
 * - INACTIVIDAD_TIMEOUT: Tiempo en milisegundos antes de mostrar el modal (5 segundos para testing)
 * - CUENTA_REGRESIVA: Tiempo en segundos para la cuenta regresiva (10 segundos)
 * - LOGOUT_URL: URL para cerrar sesión
 */

(function() {
    'use strict';

    // ============================================
    // CONFIGURACIÓN
    // ============================================
    const INACTIVIDAD_TIMEOUT = 300000; // 5 minutos de inactividad (300000 ms = 5 min × 60 seg × 1000 ms)
    const CUENTA_REGRESIVA = 10; // 10 segundos de cuenta regresiva
    const LOGOUT_URL = '/prueba/logout/'; // URL de logout

    // ============================================
    // VARIABLES GLOBALES
    // ============================================
    let timeoutInactividad = null;
    let timeoutCuentaRegresiva = null;
    let cuentaRegresivaRestante = CUENTA_REGRESIVA;
    let modalVisible = false;
    let esActivo = true;

    // ============================================
    // FUNCIONES DE DETECCIÓN DE ACTIVIDAD
    // ============================================
    
    /**
     * Reinicia el temporizador de inactividad cuando detecta actividad del usuario.
     * NO cierra el modal si está visible - solo se cierra con el botón.
     */
    function reiniciarTemporizador() {
        // Si hay un modal visible, NO hacer nada - el modal solo se cierra con el botón
        if (modalVisible) {
            return; // No reiniciar el temporizador mientras el modal está visible
        }

        // Limpiar el temporizador anterior
        if (timeoutInactividad) {
            clearTimeout(timeoutInactividad);
        }

        // Marcar como activo
        esActivo = true;

        // Establecer nuevo temporizador
        timeoutInactividad = setTimeout(mostrarModalInactividad, INACTIVIDAD_TIMEOUT);
    }

    /**
     * Crea y muestra el modal de inactividad con cuenta regresiva.
     */
    function mostrarModalInactividad() {
        // No mostrar si el modal ya está visible
        if (modalVisible) {
            return;
        }

        modalVisible = true;
        esActivo = false;
        cuentaRegresivaRestante = CUENTA_REGRESIVA;

        // Crear el modal si no existe
        if (!document.getElementById('modal-inactividad-overlay')) {
            crearModalInactividad();
        }

        // Mostrar el modal
        const overlay = document.getElementById('modal-inactividad-overlay');
        const modal = document.getElementById('modal-inactividad');
        
        // Verificar que los elementos existan antes de mostrarlos
        if (!overlay || !modal) {
            console.error('Error: No se pudo encontrar el overlay o el modal de inactividad');
            return;
        }
        
        overlay.style.display = 'flex';
        modal.style.display = 'block';
        
        // Asegurar que el overlay tenga z-index alto
        overlay.style.zIndex = '10003';

        // Resetear el contador a su color inicial (amarillo) antes de iniciar la cuenta regresiva
        const contador = document.getElementById('contador-inactividad');
        if (contador) {
            contador.style.color = 'var(--color-warning)'; // Color amarillo inicial
            contador.style.animation = 'none'; // Quitar cualquier animación previa
            // Forzar reflow para resetear la animación
            void contador.offsetWidth;
        }

        // Iniciar cuenta regresiva
        iniciarCuentaRegresiva();
    }

    /**
     * Cierra el modal de inactividad y reinicia el temporizador.
     */
    function cerrarModalInactividad() {
        if (!modalVisible) {
            return;
        }

        modalVisible = false;
        esActivo = true;

        // Cancelar cuenta regresiva
        if (timeoutCuentaRegresiva) {
            clearTimeout(timeoutCuentaRegresiva);
            timeoutCuentaRegresiva = null;
        }

        // Ocultar modal
        const overlay = document.getElementById('modal-inactividad-overlay');
        const modal = document.getElementById('modal-inactividad');
        if (overlay) {
            overlay.style.display = 'none';
        }
        if (modal) {
            modal.style.display = 'none';
        }

        // Reiniciar temporizador de inactividad
        reiniciarTemporizador();
    }

    /**
     * Crea el HTML del modal de inactividad.
     */
    function crearModalInactividad() {
        const overlay = document.createElement('div');
        overlay.id = 'modal-inactividad-overlay';
        overlay.className = 'modal-overlay modal-inactividad-overlay';
        
        const modal = document.createElement('div');
        modal.id = 'modal-inactividad';
        modal.className = 'modal-content modal-small';
        
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
        
        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        // Event listener para el botón de continuar - ÚNICA forma de cerrar el modal
        const btnContinuar = document.getElementById('btn-continuar-sesion');
        if (btnContinuar) {
            btnContinuar.addEventListener('click', cerrarModalInactividad);
        }

        // NO cerrar al hacer clic en el overlay - el modal solo se cierra con el botón
        // Prevenir que el clic en el overlay cierre el modal
        overlay.addEventListener('click', function(e) {
            // Si se hace clic directamente en el overlay (no en el modal), no hacer nada
            if (e.target === overlay) {
                e.stopPropagation();
                e.preventDefault();
            }
        });
        
        // Prevenir que se cierre el modal al hacer clic en el contenido del modal
        modal.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }

    /**
     * Inicia la cuenta regresiva y actualiza el contador cada segundo.
     * Al llegar a 0, redirige al logout.
     */
    function iniciarCuentaRegresiva() {
        const contador = document.getElementById('contador-inactividad');
        
        // Actualizar contador inmediatamente y asegurar color inicial
        if (contador) {
            contador.textContent = cuentaRegresivaRestante;
            // Asegurar que el color inicial sea amarillo si el contador es mayor a 3
            if (cuentaRegresivaRestante > 3) {
                contador.style.color = 'var(--color-warning)'; // Color amarillo
                contador.style.animation = 'none'; // Sin animación
            }
        }

        // Función recursiva para actualizar cada segundo
        function actualizarCuenta() {
            cuentaRegresivaRestante--;

            // Actualizar el contador en el DOM
            if (contador) {
                contador.textContent = cuentaRegresivaRestante;
                
                // Cambiar color cuando quedan 3 segundos o menos
                if (cuentaRegresivaRestante <= 3) {
                    contador.style.color = 'var(--color-danger)'; // Color rojo
                    contador.style.animation = 'pulse 0.5s infinite';
                } else {
                    // Mantener color amarillo si es mayor a 3
                    contador.style.color = 'var(--color-warning)'; // Color amarillo
                    contador.style.animation = 'none'; // Sin animación
                }
            }

            // Si llegó a 0, cerrar sesión
            if (cuentaRegresivaRestante <= 0) {
                // Redirigir a logout
                window.location.href = LOGOUT_URL;
                return;
            }

            // Si el modal sigue visible, continuar la cuenta regresiva
            if (modalVisible) {
                timeoutCuentaRegresiva = setTimeout(actualizarCuenta, 1000);
            }
        }

        // Iniciar cuenta regresiva después de 1 segundo
        timeoutCuentaRegresiva = setTimeout(actualizarCuenta, 1000);
    }

    // ============================================
    // EVENTOS DE ACTIVIDAD DEL USUARIO
    // ============================================
    
    // Eventos que indican actividad del usuario para evitar que se cierre la sesión
    const eventosActividad = [
        'mousedown',
        'mousemove',
        'keypress',
        'scroll',
        'touchstart',
        'click'
    ];

    // Agregar event listeners para detectar actividad
    eventosActividad.forEach(function(evento) {
        document.addEventListener(evento, reiniciarTemporizador, true);
    });

    // También detectar actividad cuando la ventana recibe el foco
    window.addEventListener('focus', reiniciarTemporizador);

    // ============================================
    // INICIALIZACIÓN
    // ============================================
    
    /**
     * Inicializa el detector de inactividad cuando el DOM está listo.
     */
    function inicializar() {
        // Solo inicializar si no estamos en la página de login
        const rutaActual = window.location.pathname;
        const esLogin = rutaActual.includes('/login/') || 
                       rutaActual === '/' || 
                       rutaActual === '/prueba/' ||
                       rutaActual.endsWith('/login');
        
        if (esLogin) {
            return; // No activar en login
        }

        // Verificar que el DOM esté completamente cargado
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                reiniciarTemporizador();
            });
        } else {
            // DOM ya está listo
            reiniciarTemporizador();
        }
    }

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializar);
    } else {
        // DOM ya está listo
        inicializar();
    }

    // También inicializar después de que todos los scripts se hayan cargado
    // Esto asegura que funcione incluso si el script se carga de forma asíncrona
    if (window.addEventListener) {
        window.addEventListener('load', function() {
            // Re-inicializar solo si no se ha iniciado ya
            if (!timeoutInactividad) {
                inicializar();
            }
        });
    }

    // Reiniciar cuando la página se vuelve visible (el usuario vuelve a la pestaña)
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden && esActivo) {
            reiniciarTemporizador();
        }
    });

})();

