// ============================================
// Script común para cargar tema oscuro en todas las páginas
// ============================================

(function() {
    'use strict';
    
    // Función para cargar el tema desde localStorage
    function cargarTema() {
        const temaOscuro = localStorage.getItem('temaOscuro') === 'true';
        if (temaOscuro) {
            document.body.classList.add('dark-theme');
        } else {
            document.body.classList.remove('dark-theme');
        }
    }
    
    // Aplicar tema inmediatamente (antes de que se renderice la página)
    // Esto previene el "flash" de contenido claro
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', cargarTema);
    } else {
        cargarTema();
    }
    
    // También aplicar al cargar completamente
    window.addEventListener('load', cargarTema);
})();

