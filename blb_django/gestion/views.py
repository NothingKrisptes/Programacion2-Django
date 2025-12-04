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
    pass

def crear_libro(request):
    pass

def lista_autores(request):
    autores = Autor.objects.all() #Devuelve toda la lista 
    return render(request, 'gestion/templates/autores.html',{'autores':autores})

def crear_autor(request):
    pass

def lista_prestamos(request):
    pass

def crear_prestamo(request):
    pass

def detalle_prestamo(request):
    pass

def lista_multas (request):
    pass

def crear_multa(request):
    pass