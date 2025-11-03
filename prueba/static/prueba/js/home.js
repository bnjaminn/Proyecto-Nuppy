// ============================================
// JavaScript para el módulo de ingreso de calificaciones
// Maneja ambos modales: ingreso y factores
// ============================================

// Función helper para obtener el CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Obtener CSRF token
const csrftoken = getCookie('csrftoken');

// URLs (se deben pasar desde el template usando data attributes o variables globales)
// Por ahora usaremos URLs relativas que Django puede procesar

// Esperar a que el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    
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
    const modal1Dividendo = document.getElementById('modal-dividendo');
    const modal1ISFUT = document.getElementById('modal-isfut');
    
    // Campos del dashboard
    const dashboardMercado = document.getElementById('mercado');
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

    // --- Funciones para abrir/cerrar Modal 1 ---
    function abrirModal1() { 
        // Copia el valor actual Mercado y Año del dashboard al campo del modal
        if (modal1Mercado && dashboardMercado) {
            modal1Mercado.value = dashboardMercado.value; 
        }
        const anhoValor = dashboardPeriodo ? dashboardPeriodo.value : new Date().getFullYear();
        if (modal1Anho) modal1Anho.value = anhoValor;
        if (modal1Ejercicio) modal1Ejercicio.value = anhoValor;
        // Muestra el modal cambiando su estilo CSS
        if (modalOverlay1) modalOverlay1.style.display = 'flex'; 
    }
    
    function cerrarModal1() { 
        // Oculta el modal
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
    
    if (btnSiguienteModal) {
        btnSiguienteModal.addEventListener('click', function() {
            // Validar campos mínimos requeridos
            if (!modal1Instrumento || !modal1Instrumento.value.trim()) {
                alert('El campo Instrumento es obligatorio');
                return;
            }
            if (!modal1Secuencia || !modal1Secuencia.value || parseInt(modal1Secuencia.value) <= 10000) {
                alert('La secuencia de evento debe ser mayor a 10,000');
                return;
            }

            // Preparar FormData con todos los campos
            const formData = new FormData();
            formData.append('Mercado', modal1Mercado ? modal1Mercado.value || '' : '');
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
                    alert('Error: ' + (data.error || 'No se pudo crear la calificación'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al enviar los datos. Por favor, intente nuevamente.');
            });
        });
    }

    // Evento para cerrar el modal si se hace clic en el fondo
    if (modalOverlay1) {
        modalOverlay1.addEventListener('click', (e) => { 
            if (e.target === modalOverlay1) {
                cerrarModal1();
            }
        });
    }

    // ========== MODAL 2 (Factores) ==========
    const modalOverlay2 = document.getElementById('factores-modal-overlay');
    const btnCerrarModal2 = document.getElementById('btn-cerrar-modal-factores');
    const btnCerrarModal2X = document.getElementById('btn-cerrar-modal-factores-x');
    const btnGrabarFactores = document.getElementById('btn-grabar-factores');

    // Obtener URLs desde window.DJANGO_URLS (configurado en el template)
    const guardarFactoresUrl = window.DJANGO_URLS ? window.DJANGO_URLS.guardarFactores : '/guardar-factores/';

    function abrirModal2(data) {
        // Llenar campos del modal de factores con los datos recibidos
        const calificacionId = document.getElementById('calificacion_id');
        if (calificacionId) calificacionId.value = data.calificacion_id;
        
        const factoresMercado = document.getElementById('factores-mercado');
        if (factoresMercado) factoresMercado.value = data.data.mercado || '';
        
        const factoresInstrumento = document.getElementById('factores-instrumento');
        if (factoresInstrumento) factoresInstrumento.value = data.data.instrumento || '';
        
        const factoresEventoCapital = document.getElementById('factores-evento_capital');
        if (factoresEventoCapital) factoresEventoCapital.value = data.data.evento_capital || '';
        
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
        
        if (modalOverlay2) modalOverlay2.style.display = 'flex';
    }

    function cerrarModal2() {
        if (modalOverlay2) modalOverlay2.style.display = 'none';
    }

    if (btnCerrarModal2) {
        btnCerrarModal2.addEventListener('click', cerrarModal2);
    }
    if (btnCerrarModal2X) {
        btnCerrarModal2X.addEventListener('click', cerrarModal2);
    }

    if (modalOverlay2) {
        modalOverlay2.addEventListener('click', (e) => {
            if (e.target === modalOverlay2) {
                cerrarModal2();
            }
        });
    }

    // Botón Grabar
    if (btnGrabarFactores) {
        btnGrabarFactores.addEventListener('click', function() {
            const formFactores = document.getElementById('form-factores');
            if (!formFactores) {
                alert('Error: No se encontró el formulario de factores');
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
                    alert('Factores guardados exitosamente');
                    cerrarModal2();
                    // Recargar la página para ver los cambios
                    window.location.reload();
                } else {
                    alert('Error: ' + (data.error || 'No se pudieron guardar los factores'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al guardar. Por favor, intente nuevamente.');
            });
        });
    }
});

