# Librerias para hacer los test en views
from django.urls import reverse
from django.test import TestCase
from gestion.models import Libro, Autor

class ListaLibroViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        autor = Autor.objects.create(nombre = "Autor", apellido = "Libro", bibliografia = "BBBBBB")
        for i in range(3):
            Libro.objects.create(titulo =f"I Robot{i}", autor = autor, disponible = True)
            
    def test_url_existencias(self):
        resp = self.client.get(reverse('lista_libros')) #client simula ser un cliente web algo asi xD
        self.assertEqual(resp.status_code, 200) #Valida que la respuesta sea 200
        self.assertTemplateUsed (resp, 'gestion/templates/libros.html') #Valida que el template que esta usando al validar libros sea la que efectivamente se este usando
        self.assertEqual(len(resp.context['libros']), 3)