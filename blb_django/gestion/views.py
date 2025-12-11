from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.conf import settings
from .models import Autor,Libro,Prestamo,Multa
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy

# Create your views here.

def index(request): #request devuelve respuesta en el navegador
    title = settings.TITLE
    return render(request,'gestion/templates/home.html', {'titulo': title})

def lista_libros(request):
    libros = Libro.objects.all() #Devuelve toda la lista 
    return render(request, 'gestion/templates/libros.html',{'libros':libros})

def crear_libro(request):
    autores = Autor.objects.all()

    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        autor_id = request.POST.get('autor')
        
        if titulo and autor_id:
            autor = get_object_or_404(Autor, id=autor_id)
            Libro.objects.create(titulo=titulo, autor=autor)
            return redirect(lista_libros)
    return render(request, 'gestion/templates/crear_libros.html', {'autores':autores})

# def editar_autores(request, id):
#     autor = get_object_or_404(Autor, id=id) #Tenemos que comparar con la variable que se va a editar
#     if request.method == 'POST':
#         nombre = request.POST.get('nombre')
#         apellido = request.POST.get('apellido')
#         bibliografia = request.POST.get('bibliografia')
        
#         if nombre and apellido:
#             autor.apellido = apellido
#             autor.nombre = nombre
#             autor.bibliografia = bibliografia
#             autor.save()
#             return redirect('lista_autores')
#     return render(request, 'gestion/templates/editar_autores.html',{'autor':autor})
       
def lista_autores(request):
    autores = Autor.objects.all() #Devuelve toda la lista 
    return render(request, 'gestion/templates/autores.html',{'autores':autores})

@login_required
def crear_autor(request, id=None):
    if id == None:
        autor = None
        modo = 'Crear'
    else:
        autor = get_object_or_404(Autor, id=id)
        modo = 'Editar'
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        bibliografia = request.POST.get('bibliografia')
        if autor == None:
            Autor.objects.create(nombre=nombre, apellido=apellido, bibliografia=bibliografia)
        else:
            autor.apellido = apellido
            autor.nombre = nombre
            autor.bibliografia = bibliografia
            autor.save()
        return redirect(lista_autores)
    context = {'autor':autor,
               'titulo':'Editar Autor'if modo == 'Editar' else 'Crear Autor',
               'texto_boton': 'Guardar cambios' if modo == 'Editar' else 'Crear'}
    return render(request, 'gestion/templates/crear_autores.html', context)

def lista_prestamos(request):
    prestamos = Prestamo.objects.all() #Devuelve toda la lista 
    return render(request, 'gestion/templates/prestamos.html',{'prestamos':prestamos})

# def crear_prestamo(request):
#     libros = Libro.objects.all()
#     usuarios = User.objects.all()
    
#     if request.method == 'POST':
#         libro_id = request.POST.get('titulo')
#         usuario_id = request.POST.get('autor')
#         fecha_prestamos = request.POST.get('fecha_prestamos')
#         fecha_max = request.POST.get('fecha_max')
#         fecha_devolucion = request.POST.get('fecha_devolucion')
        
#         if libro_id and usuario_id:
#             libro = get_object_or_404(Libro, id = libro_id)
#             usuario = get_object_or_404(User, id = usuario_id)
#             Prestamo.objects.create(libro=libro, usuario=usuario, fecha_prestamos = fecha_prestamos, 
#                                     fecha_max = fecha_max, fecha_devolucion = fecha_devolucion)
#             return redirect(lista_prestamos)
#     return render(request, 'gestion/templates/crear_prestamos.html', {'libros':libros}, {'usuarios': usuarios})

@login_required
def crear_prestamos(request):
    if not request.user.has_perm('gestion.gestionar_prestamos'):
        return HttpResponseForbidden()
    
    libro = Libro.objects.filter(disponible=True)
    usuario = User.objects.all()
    if request.method == 'POST':
        libro_id = request.POST.get('libro')
        usuario_id = request.POST.get('usuario')
        fecha_prestamos = request.POST.get('fecha_prestamos')
        if libro_id and usuario_id and fecha_prestamos:
            libro = get_object_or_404(Libro, id=libro_id)
            usuario = get_object_or_404(User, id=usuario_id)
            prestamo = Prestamo.objects.create(libro = libro,
                                               usuario = usuario,
                                               fecha_prestamos = fecha_prestamos,)
            libro.disponible = False
            libro.save()
            return redirect('detalle_prestamo', id = prestamo)
    fecha = (timezone.now().date()).isoformat() #YYYY-MM-DD
    return render(request,'gestion/templates/crear_prestamos.html', {'libros':libro, 
                                                                    'usuario':usuario,
                                                                    'fecha': fecha})

def detalle_prestamo(request):
    pass

def lista_multas (request):
    multas = Multa.objects.all() #Devuelve toda la lista 
    return render(request, 'gestion/templates/multas.html',{'multas':multas})
def crear_multa(request):
    autores = Autor.objects.all()

    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        autor_id = request.POST.get('autor')
        
        if titulo and autor_id:
            autor = get_object_or_404(Autor, id=autor_id)
            Libro.objects.create(titulo=titulo, autor=autor)
            return redirect(lista_libros)
    return render(request, 'gestion/templates/crear_libros.html', {'autores':autores})

def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            try:
                permiso = Permission.objects.get(codename='gestionar_prestamos')
                usuario.user_permissions.add(permiso)
            except Permission.DoesNotExist:
                return redirect('error')
            login(request, usuario)
            return redirect('index')
    else:
        form = UserCreationForm()   
    return render(request, 'gestion/templates/registration/registro.html', {'form': form})

def error(request):
    return render(request, 'gestion/templates/error.html',{'error':error})

# TIPO DE VISTAS VERSION DJGANGO
# Se necesitan las siguientes librerias
# from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
# from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
# from django.urls import reverse_lazy

class LibroListView(LoginRequiredMixin, ListView):
    model = Libro
    template_name = 'gestion/templates/libros_view.html'
    context_object_name = 'libros'
    paginate_by = 1 # Lista primaria de 10 objetos que se puede ir recorriendo "pestañas de paginas"
    
class LibroDetalleView(LoginRequiredMixin, DetailView):
    model = Libro
    template_name = 'gestion/templates/detalle_libros.html'
    context_object_name = 'libro'
    
class LibroCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Libro
    fields = ['titulo', 'autor', 'disponible']
    template_name = 'gestion/templates/crear_libros.html'
    success_url = reverse_lazy('libro_list') #Direcciona a la url que eligamos
    permission_required = 'gestion.add_libro'

class LibroUpdateView(LoginRequiredMixin,PermissionRequiredMixin, UpdateView):
    model = Libro
    fields = ['titulo', 'autor']
    template_name = 'gestion/templates/editar_libros.html'
    success_url = reverse_lazy('libro_list')
    permission_required = 'gestion.change_libro'
    
class LibroDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Libro
    template_name = 'gestion/templates/eliminar_libros.html' # Ventana de confirmacion para eliminar
    success_url = reverse_lazy('libro_list')
    permission_required = 'gestion.delete_libro'
    