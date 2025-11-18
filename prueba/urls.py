from django.urls import path, include
from .views import listar_usuarios, login_view, home_view, logout_view, ingresar_view, administrar_view, crear_usuario_view, eliminar_usuarios_view, obtener_usuario_view, modificar_usuario_view, ver_logs_view, guardar_factores_view, calcular_factores_view, buscar_calificaciones_view
urlpatterns = [
    path("listar/", listar_usuarios, name = "listar_usuarios"),
    path('home/', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('ingresar/', ingresar_view, name='ingresar'),
    path('guardar-factores/', guardar_factores_view, name='guardar_factores'),
    path('calcular-factores/', calcular_factores_view, name='calcular_factores'),
    path('buscar-calificaciones/', buscar_calificaciones_view, name='buscar_calificaciones'),
    path('administrar/', administrar_view, name='administrar'),
    path('crear_usuario/', crear_usuario_view, name='crear_usuario'),
    path('eliminar_usuarios/', eliminar_usuarios_view, name='eliminar_usuarios'),
    path('obtener-usuario/<str:user_id>/', obtener_usuario_view, name='obtener_usuario'),
    path('modificar-usuario/', modificar_usuario_view, name='modificar_usuario'),
    path('ver-logs/', ver_logs_view, name='ver_logs'),
]
