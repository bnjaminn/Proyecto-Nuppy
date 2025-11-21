// ============================================
// TEMA.JS - Gestión de Tema Oscuro/Claro
// ============================================
// Este script gestiona el tema oscuro/claro de la aplicación.
// La preferencia del usuario se guarda en localStorage para persistir entre sesiones.
// Se ejecuta inmediatamente al cargar para prevenir el "flash" de contenido claro.
// ============================================

(function() {
    'use strict';
    
    // ============================================
    // FUNCIÓN: cargarTema()
    // ============================================
    // Propósito: Carga la preferencia de tema desde localStorage y aplica las clases CSS correspondientes.
    // 
    // Flujo de ejecución:
    // 1. Lee el valor 'temaOscuro' desde localStorage
    // 2. Si es 'true', agrega la clase 'dark-theme' al body
    // 3. Si es 'false' o no existe, remueve la clase 'dark-theme' del body
    // 
    // La clase 'dark-theme' activa los estilos CSS del tema oscuro definidos en los archivos CSS.
    // 
    // Retorna: void (no retorna nada, solo modifica el DOM)
    // ============================================
    function cargarTema() {
        // Leer preferencia desde localStorage (devuelve 'true' o 'false' como string, o null si no existe)
        const temaOscuro = localStorage.getItem('temaOscuro') === 'true';
        
        if (temaOscuro) {
            // Usuario prefiere tema oscuro: agregar clase CSS al body
            // Esto activará todos los estilos definidos en CSS para .dark-theme
            document.body.classList.add('dark-theme');
        } else {
            // Usuario prefiere tema claro o no tiene preferencia: remover clase
            // Esto mantendrá los estilos por defecto (tema claro)
            document.body.classList.remove('dark-theme');
        }
    }
    
    // ============================================
    // APLICAR TEMA INMEDIATAMENTE
    // ============================================
    // Se ejecuta ANTES de que el contenido sea visible para prevenir el "flash" de contenido claro.
    // 
    // La estrategia es verificar el estado del documento:
    // - Si está 'loading': esperar al evento DOMContentLoaded
    // - Si ya está cargado: aplicar el tema inmediatamente
    // 
    // Esto asegura que el tema se aplique antes de que el usuario vea cualquier contenido.
    // ============================================
    if (document.readyState === 'loading') {
        // El documento aún se está cargando: esperar a que esté listo
        // DOMContentLoaded se dispara cuando el HTML está completamente cargado y parseado
        document.addEventListener('DOMContentLoaded', cargarTema);
    } else {
        // El documento ya está cargado: aplicar tema inmediatamente
        // Esto puede pasar si el script se carga después de que el DOM ya está listo
        cargarTema();
    }
    
    // Aplicar tema también al evento 'load' (cuando todos los recursos están cargados)
    // Esto asegura que el tema se aplique incluso si el script se carga muy tarde
    window.addEventListener('load', cargarTema);
})();

