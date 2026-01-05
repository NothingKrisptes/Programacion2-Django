# Librerias para hacer los test en views
from datetime import timedelta
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.utils import timezone
from gestion.models import Autor, Libro, Prestamo, Multa

# class ListaLibroViewTest(TestCase):
#     @classmethod
#     def setUpTestData(cls):
#         autor = Autor.objects.create(nombre = "Autor", apellido = "Libro", bibliografia = "BBBBBB")
#         for i in range(3):
#             Libro.objects.create(titulo =f"I Robot{i}", autor = autor, disponible = True)
            
#     def test_url_existencias(self):
#         resp = self.client.get(reverse('lista_libros')) #client simula ser un cliente web algo asi xD
#         self.assertEqual(resp.status_code, 200) #Valida que la respuesta sea 200
#         self.assertTemplateUsed (resp, 'gestion/templates/libros.html') #Valida que el template que esta usando al validar libros sea la que efectivamente se este usando
#         self.assertEqual(len(resp.context['libros']), 3)

# Nuevos tests unitarios:

class LoginRequiredViewsTest(TestCase):
    """Verifica que páginas sensibles redirigen si no hay login."""
    def test_libros_inactivos_redirige_sin_login(self):
        resp = self.client.get(reverse("libros_inactivos"))
        self.assertEqual(resp.status_code, 302)

    def test_crear_multa_redirige_sin_login(self):
        resp = self.client.get(reverse("crear_multa"))
        self.assertEqual(resp.status_code, 302)

class SoftDeleteLibroTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("u1", password="test123456.")
        cls.autor = Autor.objects.create(nombre="Autor", apellido="Demo")
        cls.libro = Libro.objects.create(titulo="Libro X", autor=cls.autor, stock=2, activo=True)

        # Dar permiso delete_libro al usuario para que no devuelva 403
        perm = Permission.objects.get(codename="delete_libro")
        cls.user.user_permissions.add(perm)

    def test_inactivar_libro_por_deleteview_post(self):
        self.client.login(username="u1", password="test123456.")
        resp = self.client.post(reverse("eliminar_libro", kwargs={"pk": self.libro.pk}))
        self.assertEqual(resp.status_code, 302)

        self.libro.refresh_from_db()
        self.assertFalse(self.libro.activo)

    def test_deleteview_sin_permiso_da_403(self):
        user2 = User.objects.create_user("u2", password="xxx")
        self.client.login(username="u2", password="xxx")
        resp = self.client.post(reverse("eliminar_libro", kwargs={"pk": self.libro.pk}))
        self.assertEqual(resp.status_code, 403)

class CrearMultaTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("u1", password="test123456.")
        cls.autor = Autor.objects.create(nombre="Julio", apellido="Verne")
        cls.libro = Libro.objects.create(titulo="Viaje", autor=cls.autor, stock=1, activo=True)

        hoy = timezone.now().date()
        cls.prestamo = Prestamo.objects.create(
            libro=cls.libro,
            usuario=cls.user,
            fecha_prestamos=hoy,
            fecha_max=hoy - timedelta(days=4),  # retraso 4
            fecha_devolucion=hoy,
        )

    def test_crear_multa_deterioro_suma_retraso_y_extra(self):
        self.client.login(username="u1", password="test123456.")

        # deterioro +10, con retraso>0
        resp = self.client.post(
            reverse("crear_multa"),
            data={"prestamo": self.prestamo.id, "tipo": "d", "extra": "10.00"},
            follow=False
        )
        self.assertEqual(resp.status_code, 302)

        multa = Multa.objects.latest("id")
        self.assertEqual(multa.prestamo_id, self.prestamo.id)
        self.assertEqual(multa.tipo, "d")
        # base=4*0.50=2.00; extra=10.00 => 12.00
        self.assertEqual(multa.monto, Decimal("12.00"))

class CrearMultaTemplateDisabledOptionTest(TestCase):
    """Asegura que los préstamos con libro inactivo aparecen disabled en el select"""
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("u1", password="test123456.")
        cls.autor = Autor.objects.create(nombre="Autor", apellido="Demo")

        cls.libro_inactivo = Libro.objects.create(titulo="L inactivo", autor=cls.autor, stock=1, activo=False)
        cls.libro_activo = Libro.objects.create(titulo="L activo", autor=cls.autor, stock=1, activo=True)

        hoy = timezone.now().date()
        cls.prestamo_inactivo = Prestamo.objects.create(
            libro=cls.libro_inactivo,
            usuario=cls.user,
            fecha_prestamos=hoy,
            fecha_max=hoy,
        )
        cls.prestamo_activo = Prestamo.objects.create(
            libro=cls.libro_activo,
            usuario=cls.user,
            fecha_prestamos=hoy,
            fecha_max=hoy,
        )

    def test_option_disabled_para_libro_inactivo(self):
        self.client.login(username="u1", password="test123456.")
        resp = self.client.get(reverse("crear_multa"))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode("utf-8")
        # Debe contener el texto [INACTIVO]
        self.assertIn("[INACTIVO]", html)
        # Y el option del préstamo inactivo debe estar disabled
        self.assertIn(f'value="{self.prestamo_inactivo.id}" disabled', html)