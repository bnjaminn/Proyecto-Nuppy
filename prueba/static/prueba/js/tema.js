/**
 * TEMA.JS - Gestión de Tema Oscuro/Claro
 * ============================================
 * 
 * POR QUÉ ESTE SCRIPT ES IMPORTANTE:
 * - Permite a los usuarios elegir entre tema oscuro y claro
 * - Mejora la experiencia de usuario (reduce fatiga visual en ambientes oscuros)
 * - La preferencia se guarda en localStorage (persiste entre sesiones)
 * - Se ejecuta ANTES de que el contenido sea visible (previene "flash" de contenido claro)
 * 
 * CÓMO FUNCIONA:
 * 1. Al cargar la página, lee la preferencia guardada en localStorage
 * 2. Si el usuario prefiere tema oscuro, agrega la clase 'dark-theme' al body
 * 3. Si prefiere tema claro o no tiene preferencia, mantiene el tema claro (sin clase)
 * 4. La clase 'dark-theme' activa los estilos CSS del tema oscuro
 * 
 * FLASH DE CONTENIDO:
 * - Sin este script, el usuario vería un "flash" de contenido claro antes de aplicar el tema oscuro
 * - Este script se ejecuta ANTES de que el contenido sea visible
 * - Verifica el estado del documento y aplica el tema inmediatamente
 * 
 * PERSISTENCIA:
 * - localStorage guarda la preferencia en el navegador del usuario
 * - La preferencia persiste entre sesiones (no se pierde al cerrar el navegador)
 * - Otros scripts pueden cambiar el tema actualizando localStorage y llamando cargarTema()
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
    // FUNCIÓN: cargarTema()
    // ============================================
    /**
     * Carga la preferencia de tema desde localStorage y aplica las clases CSS correspondientes.
     * 
     * POR QUÉ ESTA FUNCIÓN ES NECESARIA:
     * - Lee la preferencia guardada del usuario
     * - Aplica el tema correcto al body del documento
     * - Se puede llamar desde otros scripts para cambiar el tema dinámicamente
     * 
     * CÓMO FUNCIONA:
     * 1. Lee el valor 'temaOscuro' desde localStorage
     * 2. Si es 'true', agrega la clase 'dark-theme' al body
     * 3. Si es 'false' o no existe, remueve la clase 'dark-theme' del body
     * 
     * La clase 'dark-theme' activa los estilos CSS del tema oscuro definidos en los archivos CSS.
     * 
     * Retorna: void (no retorna nada, solo modifica el DOM)
     */
    function cargarTema() {
        // Leer preferencia desde localStorage
        // POR QUÉ: localStorage guarda la preferencia del usuario entre sesiones
        // CÓMO: getItem() obtiene el valor guardado con la clave 'temaOscuro'
        // LÓGICA: localStorage guarda strings, así que 'true' es el string "true", no el booleano true
        // Comparación: === 'true' convierte el string a booleano (si es "true" → true, si es "false" o null → false)
        const temaOscuro = localStorage.getItem('temaOscuro') === 'true';
        
        // Aplicar tema según la preferencia
        // POR QUÉ: Necesitamos agregar o remover la clase CSS según la preferencia
        // CÓMO: classList permite agregar o remover clases CSS de un elemento
        if (temaOscuro) {
            // Usuario prefiere tema oscuro: agregar clase CSS al body
            // POR QUÉ: La clase 'dark-theme' activa todos los estilos del tema oscuro
            // CÓMO: add() agrega la clase 'dark-theme' al elemento body
            // LÓGICA: Los estilos CSS buscan la clase .dark-theme y aplican colores oscuros
            // Esto activará todos los estilos definidos en CSS para .dark-theme
            document.body.classList.add('dark-theme');
        } else {
            // Usuario prefiere tema claro o no tiene preferencia: remover clase
            // POR QUÉ: Sin la clase 'dark-theme', se aplican los estilos por defecto (tema claro)
            // CÓMO: remove() elimina la clase 'dark-theme' del elemento body
            // LÓGICA: Si no hay clase 'dark-theme', los estilos CSS usan los valores por defecto (tema claro)
            // Esto mantendrá los estilos por defecto (tema claro)
            document.body.classList.remove('dark-theme');
        }
    }
    
    // ============================================
    // APLICAR TEMA INMEDIATAMENTE
    // ============================================
    // Se ejecuta ANTES de que el contenido sea visible para prevenir el "flash" de contenido claro.
    // 
    // POR QUÉ ES CRÍTICO:
    // - Sin esto, el usuario vería un "flash" de contenido claro antes de aplicar el tema oscuro
    // - Esto crea una mala experiencia de usuario
    // - Aplicar el tema antes de que el contenido sea visible elimina este problema
    // 
    // La estrategia es verificar el estado del documento:
    // - Si está 'loading': esperar al evento DOMContentLoaded
    // - Si ya está cargado: aplicar el tema inmediatamente
    // 
    // Esto asegura que el tema se aplique antes de que el usuario vea cualquier contenido.
    
    // Verificar el estado del documento
    // POR QUÉ: Necesitamos saber si el DOM está listo para poder modificar el body
    // CÓMO: document.readyState puede ser 'loading', 'interactive', o 'complete'
    // LÓGICA: Si está 'loading', el DOM aún no está listo, debemos esperar
    if (document.readyState === 'loading') {
        // El documento aún se está cargando: esperar a que esté listo
        // POR QUÉ: No podemos modificar el body antes de que el DOM esté completamente cargado
        // CÓMO: DOMContentLoaded se dispara cuando el HTML está completamente cargado y parseado
        // LÓGICA: Cuando el DOM esté listo, ejecutamos cargarTema() para aplicar el tema
        // Esto asegura que el body existe antes de intentar agregar clases
        document.addEventListener('DOMContentLoaded', cargarTema);
    } else {
        // El documento ya está cargado: aplicar tema inmediatamente
        // POR QUÉ: Si el DOM ya está listo, no necesitamos esperar
        // CÓMO: Llamamos directamente a cargarTema()
        // LÓGICA: Esto puede pasar si el script se carga después de que el DOM ya está listo
        // En este caso, aplicamos el tema inmediatamente sin esperar eventos
        cargarTema();
    }
    
    // Aplicar tema también al evento 'load' (cuando todos los recursos están cargados)
    // POR QUÉ: Esto asegura que el tema se aplique incluso si el script se carga muy tarde
    // CÓMO: El evento 'load' se dispara cuando todos los recursos (imágenes, CSS, etc.) están cargados
    // LÓGICA: Es un respaldo por si el script se carga después de DOMContentLoaded
    // Esto garantiza que el tema se aplique en todos los casos posibles
    window.addEventListener('load', cargarTema);
    
// Cerrar la función anónima auto-ejecutable
// POR QUÉ: Esto cierra el scope privado y ejecuta la función inmediatamente
})();
