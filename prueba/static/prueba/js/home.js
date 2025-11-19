// ============================================
// JavaScript para el módulo de ingreso de calificaciones
// Maneja ambos modales: ingreso y factores (con sistema de Montos a Factores)
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

// ========== FUNCIONES PARA MODAL DE MENSAJES ==========
function mostrarMensaje(titulo, mensaje, tipo = 'info', advertencia = null) {
    const modalMensaje = document.getElementById('mensaje-modal-overlay');
    const tituloMensaje = document.getElementById('mensaje-modal-titulo');
    const textoMensaje = document.getElementById('mensaje-modal-texto');
    const iconoMensaje = document.getElementById('mensaje-modal-icono');
    const advertenciaMensaje = document.getElementById('mensaje-modal-advertencia');
    const btnCerrar = document.getElementById('btn-cerrar-mensaje');
    const btnCancelar = document.getElementById('btn-cancelar-mensaje');
    const btnConfirmar = document.getElementById('btn-confirmar-mensaje');
    
    if (!modalMensaje || !tituloMensaje || !textoMensaje || !iconoMensaje) return;
    
    // Configurar título y mensaje
    tituloMensaje.textContent = titulo;
    textoMensaje.innerHTML = mensaje; // Usar innerHTML para permitir HTML
    
    // Configurar advertencia si existe
    if (advertenciaMensaje) {
        if (advertencia) {
            advertenciaMensaje.textContent = advertencia;
            advertenciaMensaje.style.display = 'block';
        } else {
            advertenciaMensaje.style.display = 'none';
        }
    }
    
    // Configurar icono y color según el tipo
    switch(tipo) {
        case 'success':
            iconoMensaje.textContent = '✓';
            iconoMensaje.style.background = 'linear-gradient(135deg, #28A745 0%, #20C997 100%)';
            break;
        case 'error':
            iconoMensaje.textContent = '✕';
            iconoMensaje.style.background = 'linear-gradient(135deg, #DC3545 0%, #C82333 100%)';
            break;
        case 'warning':
            iconoMensaje.textContent = '⚠';
            iconoMensaje.style.background = 'linear-gradient(135deg, #FFC107 0%, #FF9800 100%)';
            break;
        default: // info
            iconoMensaje.textContent = 'ℹ';
            iconoMensaje.style.background = 'linear-gradient(135deg, #17A2B8 0%, #138496 100%)';
    }
    
    // Modo simple: un solo botón
    if (btnCerrar) btnCerrar.style.display = 'inline-block';
    if (btnCancelar) btnCancelar.style.display = 'none';
    if (btnConfirmar) btnConfirmar.style.display = 'none';
    
    // Limpiar event listeners anteriores del botón confirmar
    if (btnConfirmar) {
        const nuevoBtnConfirmar = btnConfirmar.cloneNode(true);
        btnConfirmar.parentNode.replaceChild(nuevoBtnConfirmar, btnConfirmar);
    }
    
    // Mostrar modal
    modalMensaje.style.display = 'flex';
}

function mostrarConfirmacion(titulo, mensaje, advertencia, onConfirmar, tipoBotonConfirmar = 'danger') {
    const modalMensaje = document.getElementById('mensaje-modal-overlay');
    const tituloMensaje = document.getElementById('mensaje-modal-titulo');
    const textoMensaje = document.getElementById('mensaje-modal-texto');
    const iconoMensaje = document.getElementById('mensaje-modal-icono');
    const advertenciaMensaje = document.getElementById('mensaje-modal-advertencia');
    const btnCerrar = document.getElementById('btn-cerrar-mensaje');
    const btnCancelar = document.getElementById('btn-cancelar-mensaje');
    const btnConfirmar = document.getElementById('btn-confirmar-mensaje');
    
    if (!modalMensaje || !tituloMensaje || !textoMensaje || !iconoMensaje) return;
    
    // Configurar título y mensaje
    tituloMensaje.textContent = titulo;
    textoMensaje.innerHTML = mensaje;
    
    // Configurar advertencia
    if (advertenciaMensaje) {
        if (advertencia) {
            advertenciaMensaje.textContent = advertencia;
            advertenciaMensaje.style.display = 'block';
        } else {
            advertenciaMensaje.style.display = 'none';
        }
    }
    
    // Configurar icono de advertencia
    iconoMensaje.textContent = '⚠';
    iconoMensaje.style.background = 'linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%)';
    
    // Modo confirmación: dos botones
    if (btnCerrar) btnCerrar.style.display = 'none';
    if (btnCancelar) btnCancelar.style.display = 'inline-block';
    if (btnConfirmar) {
        btnConfirmar.style.display = 'inline-block';
        // Configurar estilo del botón según el tipo
        if (tipoBotonConfirmar === 'danger') {
            btnConfirmar.className = 'btn btn-danger-modal';
        } else {
            btnConfirmar.className = 'btn';
        }
        // Configurar texto del botón
        btnConfirmar.textContent = tipoBotonConfirmar === 'danger' ? 'Eliminar' : 'Confirmar';
        // Agregar event listener
        btnConfirmar.onclick = function() {
            cerrarModalMensaje();
            if (onConfirmar) onConfirmar();
        };
    }
    
    // Mostrar modal
    modalMensaje.style.display = 'flex';
}

function cerrarModalMensaje() {
    const modalMensaje = document.getElementById('mensaje-modal-overlay');
    if (modalMensaje) {
        modalMensaje.style.display = 'none';
    }
}

// Función para inicializar los event listeners del modal de mensajes
function inicializarModalMensaje() {
    const btnCerrarMensaje = document.getElementById('btn-cerrar-mensaje');
    const btnCancelarMensaje = document.getElementById('btn-cancelar-mensaje');
    const btnCerrarMensajeX = document.getElementById('btn-cerrar-mensaje-x');
    const modalMensajeOverlay = document.getElementById('mensaje-modal-overlay');
    
    if (btnCerrarMensaje) {
        btnCerrarMensaje.addEventListener('click', cerrarModalMensaje);
    }
    if (btnCancelarMensaje) {
        btnCancelarMensaje.addEventListener('click', cerrarModalMensaje);
    }
    if (btnCerrarMensajeX) {
        btnCerrarMensajeX.addEventListener('click', cerrarModalMensaje);
    }
    if (modalMensajeOverlay) {
        modalMensajeOverlay.addEventListener('click', (e) => {
            if (e.target === modalMensajeOverlay) {
                cerrarModalMensaje();
            }
        });
    }
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
                mostrarMensaje('Campo Requerido', 'El campo Instrumento es obligatorio', 'warning');
                return;
            }
            if (!modal1Secuencia || !modal1Secuencia.value || parseInt(modal1Secuencia.value) <= 10000) {
                mostrarMensaje('Validación', 'La secuencia de evento debe ser mayor a 10,000', 'warning');
                return;
            }

            // Preparar FormData con todos los campos
            const formData = new FormData();
            formData.append('Mercado', modal1Mercado ? modal1Mercado.value || '' : '');
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
    if (modalOverlay1) {
        modalOverlay1.addEventListener('click', (e) => { 
            if (e.target === modalOverlay1) {
                cerrarModal1();
            }
        });
    }

    // ========== MODAL 2 (Factores - Montos) ==========
    const modalOverlay2 = document.getElementById('factores-modal-overlay');
    const btnCerrarModal2 = document.getElementById('btn-cerrar-modal-factores');
    const btnCerrarModal2X = document.getElementById('btn-cerrar-modal-factores-x');
    const btnGrabarFactores = document.getElementById('btn-grabar-factores');

    // Obtener URLs desde window.DJANGO_URLS (configurado en el template)
    const guardarFactoresUrl = window.DJANGO_URLS ? window.DJANGO_URLS.guardarFactores : '/guardar-factores/';
    const calcularFactoresUrl = window.DJANGO_URLS ? window.DJANGO_URLS.calcularFactores : '/calcular-factores/';

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
        
        // Ocultar sección de factores calculados al abrir
        const factoresSection = document.getElementById('factores-calculados-section');
        if (factoresSection) factoresSection.style.display = 'none';
        
        // Limpiar todos los campos de montos
        for (let i = 8; i <= 37; i++) {
            const montoInput = document.getElementById(`monto_${i}`);
            if (montoInput) montoInput.value = '0.00';
        }
        
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

    // Función para calcular Suma Base en tiempo real
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
    const buscarCalificacionesUrl = window.DJANGO_URLS ? window.DJANGO_URLS.buscarCalificaciones : '/buscar-calificaciones/';
    const tablaBody = document.getElementById('tabla-calificaciones-body');

    function formatearNumero(valor) {
        if (!valor || valor === '0' || valor === '0.0' || valor === '0.00000000') {
            return '0';
        }
        const num = parseFloat(valor);
        if (isNaN(num)) return '0';
        // Formatear con hasta 8 decimales, eliminando ceros innecesarios
        return num.toFixed(8).replace(/\.?0+$/, '');
    }

    function renderizarCalificaciones(calificaciones) {
        if (!tablaBody) return;

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
            
            // Columna de Acciones con botones con iconos SVG minimalistas (al principio)
            html += `<td class="acciones-cell">
                <button class="btn-row-icon btn-modificar-row" data-calificacion-id="${calId}" title="Modificar">
                    <svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                </button>
                <button class="btn-row-icon btn-eliminar-row" data-calificacion-id="${calId}" title="Eliminar">
                    <svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        <line x1="10" y1="11" x2="10" y2="17"></line>
                        <line x1="14" y1="11" x2="14" y2="17"></line>
                    </svg>
                </button>
                <button class="btn-row-icon btn-copiar-row" data-calificacion-id="${calId}" title="Copiar">
                    <svg class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                    </svg>
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

    // ========== FUNCIÓN PARA AGREGAR EVENT LISTENERS A BOTONES DE ACCIONES ==========
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
    }

    // ========== FUNCIÓN PARA MODIFICAR CALIFICACIÓN ==========
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
                if (modal1Mercado) modal1Mercado.value = cal.mercado || '';
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
                
                // Abrir modal 1
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

    // ========== FUNCIÓN PARA ELIMINAR CALIFICACIÓN ==========
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
                        // Recargar la tabla
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

    // ========== FUNCIÓN PARA COPIAR CALIFICACIÓN ==========
    function copiarCalificacion(calificacionId) {
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
        console.log('Copiando calificación con URL:', obtenerCalificacionUrl, 'ID:', calificacionId);
        fetch(obtenerCalificacionUrl, {
            method: 'GET',
            headers: {
                'X-CSRFToken': csrftoken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Cargar datos en el modal de ingreso (sin el ID para crear una nueva)
                const cal = data.calificacion;
                
                // Llenar campos del modal 1
                if (modal1Mercado) modal1Mercado.value = cal.mercado || '';
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
                
                // Eliminar el ID oculto si existe (para crear nueva)
                const hiddenInput = document.getElementById('calificacion-id-hidden');
                if (hiddenInput) hiddenInput.remove();
                
                // Abrir modal 1
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

    // ========== BOTÓN LIMPIAR ==========
    if (btnLimpiar) {
        btnLimpiar.addEventListener('click', function() {
            // Resetear filtros a valores por defecto
            if (dashboardMercado) dashboardMercado.value = 'chile';
            if (dashboardOrigen) dashboardOrigen.value = 'corredor';
            if (dashboardPeriodo) dashboardPeriodo.value = new Date().getFullYear().toString();

            // Limpiar tabla
            if (tablaBody) {
                tablaBody.innerHTML = `
                    <tr>
                        <td colspan="37" style="text-align: center; padding: 20px;">
                            <em>Seleccione los filtros y haga clic en "buscar" para ver las calificaciones</em>
                        </td>
                    </tr>
                `;
            }
        });
    }
});
