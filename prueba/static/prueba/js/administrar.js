// Sistema de Notificaciones Elegante
function mostrarNotificacion(mensaje, tipo = 'success') {
    // Crear contenedor de notificaciones si no existe
    let notificacionesContainer = document.getElementById('notificaciones-container');
    if (!notificacionesContainer) {
        notificacionesContainer = document.createElement('div');
        notificacionesContainer.id = 'notificaciones-container';
        document.body.appendChild(notificacionesContainer);
    }

    // Crear notificación
    const notificacion = document.createElement('div');
    notificacion.className = `notificacion notificacion-${tipo}`;
    notificacion.textContent = mensaje;
    
    // Añadir icono según tipo
    const icono = document.createElement('span');
    icono.className = 'notificacion-icono';
    if (tipo === 'success') {
        icono.textContent = '✓';
    } else if (tipo === 'error') {
        icono.textContent = '✕';
    } else if (tipo === 'warning') {
        icono.textContent = '⚠';
    } else {
        icono.textContent = 'ℹ';
    }
    notificacion.insertBefore(icono, notificacion.firstChild);

    notificacionesContainer.appendChild(notificacion);

    // Animar entrada
    setTimeout(() => notificacion.classList.add('show'), 10);

    // Auto-eliminar después de 4 segundos
    setTimeout(() => {
        notificacion.classList.remove('show');
        setTimeout(() => notificacion.remove(), 300);
    }, 4000);
}

// Sistema de Indicadores de Carga
function mostrarCarga(mensaje = 'Procesando...') {
    let overlayCarga = document.getElementById('carga-overlay');
    if (!overlayCarga) {
        overlayCarga = document.createElement('div');
        overlayCarga.id = 'carga-overlay';
        overlayCarga.innerHTML = `
            <div class="carga-spinner">
                <div class="spinner"></div>
                <p class="carga-mensaje">${mensaje}</p>
            </div>
        `;
        document.body.appendChild(overlayCarga);
    } else {
        overlayCarga.querySelector('.carga-mensaje').textContent = mensaje;
    }
    overlayCarga.style.display = 'flex';
}

function ocultarCarga() {
    const overlayCarga = document.getElementById('carga-overlay');
    if (overlayCarga) {
        overlayCarga.style.display = 'none';
    }
}

// Función para limpiar errores
function limpiarMensajeError(msg) {
    if (!msg) return "Error desconocido.";
    const lower = msg.toLowerCase();
    if (lower.includes("duplicate key") || lower.includes("correo") || lower.includes("email")) {
        return "Este correo electrónico ya está registrado.";
    } else if (lower.includes("400") || lower.includes("bad request")) {
        return "Verifica los datos ingresados. Es posible que el correo ya exista.";
    } else if (lower.includes("500")) {
        return "Error interno del servidor. Intenta más tarde.";
    } else if (lower.includes("csrf") || lower.includes("token")) {
        return "Error de seguridad. Recarga la página e inténtalo nuevamente.";
    } else if (lower.includes("json") || lower.includes("syntax")) {
        return "Error al procesar la respuesta del servidor.";
    }
    return msg.replace(/<[^>]*>?/gm, "").slice(0, 300);
}

// Espera a que TODO el HTML esté cargado y listo antes de ejecutar el código
document.addEventListener('DOMContentLoaded', function() { 
    console.log("DOM Cargado. Iniciando TODOS los scripts..."); 

    //SECCION 1: Selección/Deseleccion de Usuarios
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

    function abrirModalCrear() {
        if (!modalCrearOverlay) return;
        if (formCrearUsuario) formCrearUsuario.reset();
        modalCrearOverlay.style.display = 'flex';
    }

    function cerrarModalCrear() {
        if (!modalCrearOverlay) return;
        modalCrearOverlay.style.display = 'none';
    }

    if (btnAbrirCrear) btnAbrirCrear.addEventListener('click', abrirModalCrear);
    if (btnCerrarCrear) btnCerrarCrear.addEventListener('click', cerrarModalCrear);
    if (btnCerrarCrearX) btnCerrarCrearX.addEventListener('click', cerrarModalCrear);
    if (modalCrearOverlay) {
        modalCrearOverlay.addEventListener('click', (e) => { 
            if (e.target === modalCrearOverlay) cerrarModalCrear(); 
        });
    }
    
    if (formCrearUsuario) {
        formCrearUsuario.addEventListener('submit', function(event) {
            event.preventDefault();
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
                if (!response.ok) {
                    return response.text().then(text => { 
                        throw new Error(`Error ${response.status}: ${text}`); 
                    });
                }
                return response.json();
            })
            .then(data => {
                ocultarCarga();
                if (data.success) {
                    mostrarNotificacion('Usuario creado exitosamente!', 'success');
                    cerrarModalCrear();
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    mostrarNotificacion('Error al crear usuario: ' + (data.error || 'Intenta de nuevo.'), 'error');
                }
            })
            .catch(error => {
                ocultarCarga();
                console.error("Error detallado:", error.message);
                mostrarNotificacion("Error al crear usuario: " + limpiarMensajeError(error.message), 'error');
            });
        });
    }
    console.log("Lógica del modal Crear Usuario inicializada.");

    //SECCION 3: Eliminar Usuario
    if (btnEliminar) {
        btnEliminar.addEventListener('click', function() {
            const selectedCards = document.querySelectorAll('.user-card.selected');
            const userIdsToDelete = Array.from(selectedCards).map(card => card.dataset.userId);

            if (userIdsToDelete.length === 0) {
                mostrarNotificacion("Selecciona al menos un usuario para eliminar.", 'warning');
                return; 
            }
            if (!confirm(`¿Eliminar ${userIdsToDelete.length} usuario(s)?`)) return;

            mostrarCarga('Eliminando usuario(s)...');

            const url = window.ELIMINAR_USUARIOS_URL || '/administrar/eliminar/';
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

            if (!csrfToken) {
                ocultarCarga();
                mostrarNotificacion('Error de seguridad: No se encontró el token CSRF.', 'error');
                return;
            }

            fetch(url, {
                method: 'POST', 
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ user_ids: userIdsToDelete })
            })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => { 
                        throw new Error(`Error ${response.status}: ${text}`); 
                    });
                }
                return response.json();
            })
            .then(data => {
                ocultarCarga();
                if (data.success) {
                    mostrarNotificacion(
                        `${data.deleted_count || userIdsToDelete.length} usuario(s) eliminado(s) exitosamente.`, 
                        'success'
                    );
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    mostrarNotificacion('Error al eliminar: ' + (data.error || 'Intenta de nuevo.'), 'error');
                }
            })
            .catch(error => {
                ocultarCarga();
                console.error("Error al eliminar:", error.message);
                mostrarNotificacion('Error al eliminar usuario: ' + limpiarMensajeError(error.message), 'error');
            });
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
            mostrarNotificacion("Selecciona un usuario para modificar.", 'warning');
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
    if (modalModificarOverlay) {
        modalModificarOverlay.addEventListener('click', (e) => {
            if (e.target === modalModificarOverlay) cerrarModalModificar();
        });
    }

    if (formModificarUsuario) {
        formModificarUsuario.addEventListener('submit', function(event) {
            event.preventDefault();
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
                    mostrarNotificacion('Usuario modificado exitosamente.', 'success');
                    cerrarModalModificar();
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    mostrarNotificacion('No se pudo modificar: ' + (data.error || 'Error desconocido.'), 'error');
                }
            })
            .catch(error => {
                ocultarCarga();
                console.error("Error al modificar:", error.message);
                mostrarNotificacion('Error al modificar usuario: ' + limpiarMensajeError(error.message), 'error');
            });
        });
    }

    console.log("Script completo cargado y listeners asignados.");  
});

