from django.urls import path, include
from .views import listar_usuarios, login_view, home_view, logout_view
urlpatterns = [
    path("listar/", listar_usuarios, name = "listar_usuarios"),
    path('home/', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]
