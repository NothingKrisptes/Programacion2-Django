from django.urls import path
from .views import *

urlpatterns = [
    path("",index, name = "index"),
    
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
