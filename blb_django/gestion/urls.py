from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("",index, name = "index"),
    
    #Gestion Usuarios
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('loguot/', auth_views.LogoutView.as_view(next_page='login'),name = "logout"), #Este caso toma el valor de la pagina de login/, el name define el nombre que se usa en next_page
    
    #Cambio de contraseña
    path('password/change', auth_views.PasswordChangeView.as_view(),name="password_change"),
    path('password/change/done',auth_views.PasswordChangeDoneView.as_view(),name="password_change_done") , 
    
    #Registro
    path('registro/',registro, name="registro"),
    
    #Libros
    path('libros/',lista_libros, name="lista_libros"),
    path('libros/nuevo/',crear_libro, name="crear_libro"),
    
    #Autores
    path('autores/',lista_autores, name="lista_autores"),
    path('autores/nuevo/',crear_autor, name="crear_autores"),
    path('autores/<int:id>/editar/',crear_autor, name="editar_autores"),
    
    #Prestamos
    path('prestamos/',lista_prestamos, name="lista_prestamo"),
    path('prestamos/n/',crear_prestamos, name="crear_prestamos"),
    path('prestamos/<int:id>', detalle_prestamo, name="detalle_prestamo"),
    
    #Multas
    path('multas/',lista_multas, name="lista_multa"),
    path('multas/nuevo/<int:prestamo_id>',crear_multa, name="crear_multa"),
]
