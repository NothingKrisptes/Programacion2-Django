from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("",index, name = "index"),
    
    path("error/", error, name = "error"),
    
    # Path con class View
    #path('libros_view/', LibroListView.as_view(), name = "libros_view"),
    
    # Admin
    path("usuarios/nuevo/", nuevo_usuario, name="nuevo_usuario"),
    path("reportes/libros-prestados.pdf", reporte_libros_prestados_pdf, name="reporte_libros_prestados_pdf"),
    path("reportes/usuarios-multados.pdf", reporte_usuarios_multados_pdf, name="reporte_usuarios_multados_pdf"),
    path("reportes/multas-total.pdf", reporte_multas_total_pdf, name="reporte_multas_total_pdf"),
    path("logs/", ver_logs, name="ver_logs"),

    #Gestion Usuarios
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('loguot/', auth_views.LogoutView.as_view(next_page='login'),name = "logout"), #Este caso toma el valor de la pagina de login/, el name define el nombre que se usa en next_page
    
    #Cambio de contraseña
    path('password/change', auth_views.PasswordChangeView.as_view(),name="password_change"),
    path('password/change/done',auth_views.PasswordChangeDoneView.as_view(),name="password_change_done") , 
    
    #Registro
    path('registro/',registro, name="registro"),
    
    #Libros
    path('libros/', LibroListView.as_view(), name="lista_libros"),
    path('libros/nuevo/', LibroCreateView.as_view(), name="crear_libro"),
    path('libros/openlibrary/', buscarLibroOpenLibrary, name="buscar_libro_openlibrary"),
    path('libros/openlibrary/guardar/', guardarLibroOpenLibrary, name="guardar_libro_openlibrary"),
    path('libros/<int:pk>/editar/', LibroUpdateView.as_view(), name='editar_libro'),
    path('libros/<int:pk>/eliminar/', LibroDeleteView.as_view(), name='eliminar_libro'),
    path('libros/<int:pk>/reactivar/', reactivar_libro, name='reactivar_libro'),
    path('libros/inactivos/', LibroInactivoListView.as_view(), name='libros_inactivos'),
    
    #Autores
    path('autores/',lista_autores, name="lista_autores"),
    path('autores/nuevo/',crear_autor, name="crear_autores"),
    path('autores/<int:id>/editar/',crear_autor, name="editar_autores"),
    path("autores/<int:id>/eliminar/", inactivar_autor, name="eliminar_autor"),
    
    #Prestamos
    path('prestamos/', lista_prestamos, name="lista_prestamos"),
    path('prestamos/nuevo/', crear_prestamos, name="crear_prestamos"),
    path('prestamos/<int:id>/', detalle_prestamo, name="detalle_prestamo"),
    path('prestamos/<int:id>/devolver/', devolver_prestamo, name="devolver_prestamo"),
    
    #Multas
    path('multas/',lista_multas, name="lista_multa"),
    path('multas/nuevo/', crear_multa, name="crear_multa"),
    path('multas/nuevo/<int:prestamo_id>/', crear_multa, name="crear_multa_prestamo"),
    path('multas/<int:multaId>/pago/', multaPagoWizard, name="multa_pago_wizard"),

]
