# Creacion del testeo del models.py
# importacion de librerias para las pruebas de django

from django.test import TestCase
from gestion.models import Autor, Libro, Prestamo #Se importa los modelos con los que vamos hacer las pruebas
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

class LibroModelTest(TestCase):
    @classmethod #Configuracion o carga de datos, se carga en memoria no en la base de datos - se usa un decorador @classmethod
    def setUpTestData(cls):
        autor = Autor.objects.create(nombre ="Issac", apellido = "Asimov", bibliografia ="Cualquier dato")
        Libro.objects.create(titulo = "Fundacion", autor = autor, disponible = True) #Si una tabla depende de mas datos se crea aqui todas las pruebas que vayamos hacer y las relaciones necesarias y si hubiera mas dependecias deberia crear una variable extra o mas
    
    def test_str_devuelve_titulo(self):# Funcion para que nos devuelva el libro creado
        libro = Libro.objects.get(id = 1) #La id no es de la base de datos sino la que creamos en funcion de arriba 
        self.assertEqual(str(libro), 'Fundacion Issac Asimov') #Nos devuelve el str del modelo que configuramos en models y si no esta con los mismos parametros sale error, no se separa con ',' todo va unido


# En los test si se puede usar las secuencias de las otras clases
class PrestamoModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        autor = Autor.objects.create(nombre ="Issac", apellido = "Asimov", bibliografia ="Cualquier dato")
        usuario = User.objects.create(username='Juan', password = '#123567sd')
        libro=Libro.objects.create(titulo = "I Robot", autor = autor, disponible = False) #Si quiero hacer pasar por id y no por objecto tengo que especificarlo
        cls.prestamo = Prestamo.objects.create( #El cls es el self de la funcion creada por lo que se refresca en la otra funcion con el self
            libro=libro,
            usuario = usuario,
            fecha_max = '2025-09-28'
        )

    def test_libro_no_disponible(self): #Lo que aqui escribimos es lo que queremos hacer la prueba
        self.prestamo.refresh_from_db()
        self.assertFalse(self.prestamo.libro.disponible)
        self.assertEqual(self.prestamo.dias_retraso, 81)
        if self.prestamo.dias_retraso > 0:
            self.assertGreater(self.prestamo.multa_retraso, 0)
            
class PrestamoUsuarioViewTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user('u1', password='test123456.')
        self.user2 = User.objects.create_user('u2', password='test123456.')
        
    def test_redirige_no_login(self):
        resp = self.client.get(reverse('crear_autores'))
        self.assertEqual(resp.status_code, 302)  #Codigos de estado de respuestas es lo que hacemos referencia al usar le status_code
    
    def test_carga_login(self):
        resp = self.client.login(username="u1", password = "test123456.")
        #self.assertEqual(resp.status_code, 200)
        respl = self.client.get(reverse('crear_autores'))
        self.assertEqual(respl.status_code, 200)  #Codigos de estado de respuestas es lo que hacemos referencia al usar le status_code
    
        