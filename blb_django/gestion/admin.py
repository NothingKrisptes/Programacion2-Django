from django.contrib import admin
from .models import Autor,Libro,Prestamo,Multa
# Register your models here.

admin.site.register(Autor)
admin.site.register(Libro)
admin.site.register(Prestamo)
admin.site.register(Multa)