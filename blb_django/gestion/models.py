from django.db import models
from django.conf import settings  #Para usar los usuarios de django
from django.utils import timezone

# Create your models here.
#En django todos los campos que creemos son obligatorios
class Autor(models.Model):
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    bibliografia = models.CharField(max_length=200,blank=True, null=True)
    
    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Libro(models.Model):
    titulo = models.CharField(max_length=50)
    autor = models.ForeignKey(Autor,related_name="Libros", on_delete=models.PROTECT)    #Aqui en vez de one2many, las relaciones se hacen con llaves
    disponible = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.titulo} {self.autor}"  #En este apartado que es visual no hay que hacer makemigrations
    
class Prestamo(models.Model):
    libro = models.ForeignKey(Libro,related_name="Prestamos",on_delete=models.PROTECT)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="Prestamos", on_delete=models.PROTECT)  #Usuarios propios de Django, se importa desde el modelo de settings
    fecha_prestamos = models.DateField(default=timezone.now) #Usa la fecha del equipo actual
    fecha_max = models.DateField()
    fecha_devolucion = models.DateField(blank= True,null=True) #Para que me permita crear con datos en blanco en esta campo
    
    class Meta:
        permissions = (
            ("Ver_prestamos", "Puede ver prestamos"),
            ("gestionar_prestamos","Puede gestionar prestamos"),
            ("gestionar_libros","Puede gestionar libros"),
        )
    
    def __str__(self):
        return f"Prestamo del {self.libro} a {self.usuario}" 
    
    @property   #Nos permite trabajar con los atributos de nuestra clase seria como un compute de odoo
    def dias_retraso(self):
        hoy = timezone.now().date() #timezone zona horario, date solo la fecha
        fecha_ref = self.fecha_devolucion or hoy
        if fecha_ref > self.fecha_max:
            return (fecha_ref - self.fecha_max).days
        else:
            return 0
        
    @property
    def multa_retraso(self):
        tarifa_diaria = 0.50
        return self.dias_retraso * tarifa_diaria
    
class Multa(models.Model):
    prestamo = models.ForeignKey(Prestamo,related_name="Multas", on_delete=models.PROTECT)
    tipo = models.CharField(max_length=10, choices=(('r','retraso'),('p','perdida'),('d','deterioro'))) #Choices se debe de definir como tupla de tuplas
    monto = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    pagada = models.BooleanField(default=False)
    fecha = models.DateField(default=timezone.now)
    
    def __str__(self):
        return f"Multa {self.tipo} - {self.monto} - {self.prestamo}"
    
    def save(self, *args, **kwargs): #Los valores de args son opcionales asi que no me genera error si no se envia nada
        if self.tipo == 'r' and self.monto == 0:
            self.monto = self.prestamo.multa_retraso
        super().save(*args **kwargs) #El super es para redefinir una funcion desde la funcion padre
        

#Como django puede usar diferentes base de datos es necesario hacer una migracion para pasar de codigo py a objetos en la base de datos
#Que es ORM?
#migrate - construye mi codigo a objetos de la base de datos
#El ondelete sin restricciones elimina toda la tabla a la que esta siendo realcionada
#Primero se hace el makemigrations y luego el migrate
#python manage.py runserver para habilitar el puerto y las configuraciones de djgango
#El admitrador de django solo es un auxiliar no se deberia usar como la gestion de la base de datos, tenemos que crear vistas.
#Sql viewer instalar extension