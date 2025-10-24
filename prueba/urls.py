from django.urls import path, include
from .views import listar_usuarios, login_view, home_view, logout_view, ingresar_view, administrar_view, crear_usuario_view, eliminar_usuarios_view, obtener_usuario_view, modificar_usuario_view
urlpatterns = [
    path("listar/", listar_usuarios, name = "listar_usuarios"),
    path('home/', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('ingresar/', ingresar_view, name='ingresar'),
    path('administrar/', administrar_view, name='administrar'),
    path('crear_usuario/', crear_usuario_view, name='crear_usuario'),
    path('eliminar_usuarios/', eliminar_usuarios_view, name='eliminar_usuarios'),
    path('obtener-usuario/<str:user_id>/', obtener_usuario_view, name='obtener_usuario'),
    path('modificar-usuario/', modificar_usuario_view, name='modificar_usuario'),

]
