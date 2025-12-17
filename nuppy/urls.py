from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

# PATRONES DE URL PRINCIPALES
# ============================
urlpatterns = [
    # Redirección automática desde la raíz (/) a la página de login
    # Cuando el usuario accede a http://localhost:8000/, será redirigido a /prueba/login/
    path('', RedirectView.as_view(url='/prueba/login/', permanent=False), name='root'),
    path('admin/', admin.site.urls),
    # Incluye las URLs de la aplicación 'prueba'
    path('prueba/', include("prueba.urls")),
]

# CONFIGURACIÓN PARA SERVIR ARCHIVOS MEDIA EN DESARROLLO
# ========================================================
if settings.DEBUG:
    # Añade una ruta para servir archivos media desde el directorio MEDIA_ROOT
    # Los archivos en /media/ serán servidos desde el directorio especificado en MEDIA_ROOT
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
