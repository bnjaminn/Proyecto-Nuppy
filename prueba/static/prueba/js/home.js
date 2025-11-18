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

    // Botón Calcular
    const btnCalcularFactores = document.getElementById('btn-calcular-factores');
    if (btnCalcularFactores) {
        btnCalcularFactores.addEventListener('click', function() {
            const formFactores = document.getElementById('form-factores');
            if (!formFactores) {
                alert('Error: No se encontró el formulario de factores');
                return;
            }

            const calificacionId = document.getElementById('calificacion_id');
            if (!calificacionId || !calificacionId.value) {
                alert('Error: No se encontró el ID de la calificación');
                return;
            }

            // Enviar todos los valores del formulario para calcular
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
                        console.log('Suma 8-10:', data.debug.suma_8_a_10);
                        console.log('Suma 8-19:', data.debug.suma_8_a_19);
                        console.log('Rentas Exentas:', data.debug.rentas_exentas);
                        console.log('Factor19A:', data.debug.factor19a);
                        console.log('==============================');
                    }
                    
                    // Actualizar los campos de factores con los valores calculados
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
                                    console.log(`${fieldName}: ${input.value}`);
                                } else {
                                    input.value = value || '0';
                                    actualizados++;
                                }
                            }
                        }
                        console.log(`Total de factores actualizados: ${actualizados}`);
                    }
                    alert('Factores calculados exitosamente. Los valores han sido actualizados en el formulario.\n\nRevisa la consola del navegador (F12) para ver los detalles del cálculo.');
                } else {
                    alert('Error: ' + (data.error || 'No se pudieron calcular los factores'));
                    console.error('Error en cálculo:', data);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al calcular. Por favor, intente nuevamente.');
            });
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
                    <td colspan="37" style="text-align: center; padding: 20px;">
                        <em>No se encontraron calificaciones con los filtros seleccionados</em>
                    </td>
                </tr>
            `;
            return;
        }

        let html = '';
        calificaciones.forEach(cal => {
            html += '<tr>';
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
                        <td colspan="37" style="text-align: center; padding: 20px;">
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
                    alert('Error: ' + (data.error || 'No se pudieron buscar las calificaciones'));
                    if (tablaBody) {
                        tablaBody.innerHTML = `
                            <tr>
                                <td colspan="37" style="text-align: center; padding: 20px; color: red;">
                                    <em>Error al buscar calificaciones</em>
                                </td>
                            </tr>
                        `;
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al buscar. Por favor, intente nuevamente.');
                if (tablaBody) {
                    tablaBody.innerHTML = `
                        <tr>
                            <td colspan="37" style="text-align: center; padding: 20px; color: red;">
                                <em>Error al buscar calificaciones</em>
                            </td>
                        </tr>
                    `;
                }
            });
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

