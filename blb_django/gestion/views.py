from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

from django.conf import settings
from .models import Autor,Libro,Prestamo,Multa

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
        libro_id = request.method.POST.get('libro')
        usuario_id = request.method.POST.get('usuario')
        fecha_prestamos = request.POST.get('fecha_prestamos')
        if libro_id and usuario_id and fecha_prestamos:
            libro = get_object_or_404(Libro, id=libro_id)
            usuario = get_object_or_404(User, id=usuario_id)
            prestamo = Prestamo.objects.create(libro = libro,
                                               usuario = usuario,
                                               fecha_prestamos = fecha_prestamos)
            libro.disponible = False
            libro.save()
            return redirect('detalle_prestamo', id = prestamo.id)
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
    print('#########################')
    print(request.method)
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect ('index')
    else:
        form = UserCreationForm()
    return render(request,'gestion/templates/registration/registro.html', {'form':form})