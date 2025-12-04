from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone

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

def lista_autores(request):
    autores = Autor.objects.all() #Devuelve toda la lista 
    return render(request, 'gestion/templates/autores.html',{'autores':autores})

def crear_autor(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        bibliografia = request.POST.get('bibliografia')
        Autor.objects.create(nombre=nombre, apellido=apellido, bibliografia=bibliografia)
        return redirect(lista_autores)
    return render(request, 'gestion/templates/crear_autores.html')

def lista_prestamos(request):
    prestamos = Prestamo.objects.all() #Devuelve toda la lista 
    return render(request, 'gestion/templates/prestamos.html',{'prestamos':prestamos})

def crear_prestamo(request):
    libros = Libro.objects.all()
    usuarios = User.objects.all()
    
    if request.method == 'POST':
        libro_id = request.POST.get('titulo')
        usuario_id = request.POST.get('autor')
        fecha_prestamos = request.POST.get('fecha_prestamos')
        fecha_max = request.POST.get('fecha_max')
        fecha_devolucion = request.POST.get('fecha_devolucion')
        
        if libro_id and usuario_id:
            libro = get_object_or_404(Libro, id = libro_id)
            usuario = get_object_or_404(User, id = usuario_id)
            Prestamo.objects.create(libro=libro, usuario=usuario, fecha_prestamos = fecha_prestamos, 
                                    fecha_max = fecha_max, fecha_devolucion = fecha_devolucion)
            return redirect(lista_prestamos)
    return render(request, 'gestion/templates/crear_prestamos.html', {'libros':libros}, {'usuarios': usuarios})

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