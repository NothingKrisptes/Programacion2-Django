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
from django.contrib import messages
from .services.openLibraryService import fetchBookByTitle, OpenLibraryError # Importar el servicio de OpenLibrary
from django.views.decorators.http import require_http_methods 
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from django.db.models import F
from django.views.decorators.http import require_POST

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

#Creacion de libros con OpenLibrary  
@login_required
def buscarLibroOpenLibrary(request):
    contexto = {"data": None, "errorMsg": None, "query": "", "stock": 1}

    if request.method == "POST":
        nombreLibro = (request.POST.get("nombreLibro") or "").strip()
        contexto["query"] = nombreLibro

        # Recuperar stock del FORM 1 para poder reenviarlo luego en el FORM 2
        stock_raw = (request.POST.get("stock") or "1").strip()
        try:
            stock = int(stock_raw)
            if stock < 0:
                stock = 0
        except ValueError:
            stock = 1
        contexto["stock"] = stock

        try:
            contexto["data"] = fetchBookByTitle(nombreLibro)
        except OpenLibraryError as e:
            contexto["errorMsg"] = str(e)

    return render(request, "gestion/templates/buscar_libro_openlibrary.html", contexto)

@login_required
def guardarLibroOpenLibrary(request):
    if request.method != "POST":
        return redirect("buscar_libro_openlibrary")

    # Datos del FORM 2 (preview -> hidden inputs)
    titulo = (request.POST.get("titulo") or "").strip()
    autor_nombre = (request.POST.get("autorNombre") or "").strip()
    editorial = (request.POST.get("editorialNombre") or "").strip()
    isbn = (request.POST.get("isbn") or "").strip()
    genero = (request.POST.get("genero") or "").strip()
    descripcion = (request.POST.get("descripcion") or "").strip()
    coverId_raw = (request.POST.get("coverId") or "").strip()
    paginas_raw = (request.POST.get("paginas") or "").strip()
    stock_raw = (request.POST.get("stock") or "1").strip()

    if not titulo:
        messages.error(request, "Falta el título.")
        return redirect("buscar_libro_openlibrary")

    # Parseos seguros
    try:
        stock = int(stock_raw)
        if stock < 0:
            stock = 0
    except ValueError:
        stock = 1

    try:
        paginas = int(paginas_raw) if paginas_raw else None
    except ValueError:
        paginas = None

    try:
        coverId = int(coverId_raw) if coverId_raw else None
    except ValueError:
        coverId = None

    # Autor local (crear/buscar por nombre)
    if autor_nombre:
        partes = autor_nombre.split()
        nombre = partes[0] if partes else "Desconocido"
        apellido = " ".join(partes[1:]) if len(partes) > 1 else ""
    else:
        nombre, apellido = "Desconocido", ""

    autor, _ = Autor.objects.get_or_create(nombre=nombre, apellido=apellido)

    # --- Regla: si ya existe, sumar stock ---
    libro = None
    created = False

    # 1) Si hay ISBN, usarlo como “llave”
    if isbn:
        libro, created = Libro.objects.get_or_create(
            isbn=isbn,
            defaults={
                "titulo": titulo,
                "autor": autor,
                "paginas": paginas,
                "genero": genero or None,
                "descripcion": descripcion or None,
                "editorial": editorial or None,
                "coverId": coverId,
                "stock": stock,
                "activo": True,  # si ya agregaste soft-delete
            }
        )
        if not created:
            Libro.objects.filter(pk=libro.pk).update(stock=F("stock") + stock, activo=True)
            libro.refresh_from_db()
            libro.save()  # recalcula disponible

    # 2) Si no hay ISBN, usar titulo+autor
    else:
        libro, created = Libro.objects.get_or_create(
            titulo=titulo,
            autor=autor,
            defaults={
                "paginas": paginas,
                "genero": genero or None,
                "descripcion": descripcion or None,
                "editorial": editorial or None,
                "coverId": coverId,
                "stock": stock,
                "activo": True,  # si ya agregaste soft-delete
            }
        )
        if not created:
            Libro.objects.filter(pk=libro.pk).update(stock=F("stock") + stock, activo=True)
            libro.refresh_from_db()
            libro.save()  # recalcula disponible

    if created:
        messages.success(request, "Libro guardado correctamente.")
    else:
        messages.success(request, f"Ya existía el libro; se sumó el stock (+{stock}).")

    return redirect("lista_libros")

def lista_autores(request):
    autores = Autor.objects.all() #Devuelve toda la lista 
    return render(request, 'gestion/templates/autores.html',{'autores':autores})

@login_required
@require_POST
def reactivar_libro(request, pk):
    libro = get_object_or_404(Libro, pk=pk)
    libro.activo = True
    if libro.stock is None:
        libro.stock = 1
    libro.save()  # recalcula disponible con tu save()
    messages.success(request, "Libro reactivado correctamente.")
    return redirect("lista_libros")

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

@login_required
def lista_prestamos(request):
    prestamos = Prestamo.objects.all().order_by('-id')
    return render(request, 'gestion/templates/prestamos.html', {'prestamos': prestamos})

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
@require_http_methods(["GET", "POST"])
def crear_prestamos(request):
    if not request.user.has_perm('gestion.gestionar_prestamos'):
        return HttpResponseForbidden()

    libros = Libro.objects.filter(activo= True, stock__gt=0).order_by('titulo')
    usuarios = User.objects.all()

    if request.method == 'POST':
        libro_id = request.POST.get('libro')
        usuario_id = request.POST.get('usuario')
        fecha_prestamos_raw = (request.POST.get('fecha_prestamos') or "").strip()

        if not (libro_id and usuario_id and fecha_prestamos_raw):
            messages.error(request, "Faltan datos para crear el préstamo.")
            return redirect('crear_prestamos')

        libro = get_object_or_404(Libro, id=libro_id)
        usuario = get_object_or_404(User, id=usuario_id)

        if libro.stock <= 0:
            messages.error(request, "No hay stock disponible para este libro.")
            return redirect('crear_prestamos')

        fecha_prestamos = timezone.datetime.fromisoformat(fecha_prestamos_raw).date()
        fecha_max = fecha_prestamos + timedelta(days=7)

        prestamo = Prestamo.objects.create(
            libro=libro,
            usuario=usuario,
            fecha_prestamos=fecha_prestamos,
            fecha_max=fecha_max,
        )

        # restar stock
        Libro.objects.filter(id=libro.id).update(stock=F('stock') - 1)
        libro.refresh_from_db()
        libro.save()  # recalcula disponible

        return redirect('detalle_prestamo', id=prestamo.id)

    hoy = timezone.now().date().isoformat()
    return render(request, 'gestion/templates/crear_prestamos.html', {
        'libros': libros,
        'usuarios': usuarios,
        'fecha': hoy
    })

@login_required
def detalle_prestamo(request, id):
    prestamo = get_object_or_404(Prestamo, id=id)
    multas = prestamo.Multas.all().order_by('-id')
    return render(request, "gestion/templates/detalle_prestamo.html", {
        "prestamo": prestamo,
        "multas": multas,
    })

@login_required
@require_http_methods(["POST"])
def devolver_prestamo(request, id):
    prestamo = get_object_or_404(Prestamo, id=id)

    if prestamo.fecha_devolucion:
        return redirect("detalle_prestamo", id=prestamo.id)

    prestamo.fecha_devolucion = timezone.now().date()
    prestamo.save()

    # sumar stock
    Libro.objects.filter(id=prestamo.libro.id).update(stock=F('stock') + 1)
    prestamo.libro.refresh_from_db()
    prestamo.libro.save()  # recalcula disponible

    return redirect("detalle_prestamo", id=prestamo.id)

@login_required
def lista_multas(request):
    multas = Multa.objects.all().order_by('-id')
    return render(request, 'gestion/templates/multas.html', {'multas': multas})

@login_required
@require_http_methods(["GET", "POST"])
def crear_multa(request):
    prestamos = Prestamo.objects.all().order_by('-id')

    if request.method == "POST":
        prestamo_id = request.POST.get("prestamo")
        tipo = (request.POST.get("tipo") or "").strip()  # r, p, d
        extra_raw = (request.POST.get("extra") or "").strip()

        if not prestamo_id or tipo not in ("r", "p", "d"):
            messages.error(request, "Faltan datos o el tipo de multa es inválido.")
            return redirect("crear_multa")

        prestamo = get_object_or_404(Prestamo, id=prestamo_id)

        # BASE RETRASO: solo si hay retraso
        if prestamo.dias_retraso > 0:
            base = Decimal(str(prestamo.multa_retraso)).quantize(Decimal("0.01"))
        else:
            base = Decimal("0.00")

        extra = Decimal("0.00")

        if tipo == "d":
            # deterioro: 5 o 10 (default 5)
            try:
                extra = Decimal(extra_raw) if extra_raw else Decimal("5.00")
            except InvalidOperation:
                extra = Decimal("5.00")

            if extra not in (Decimal("5.00"), Decimal("10.00")):
                extra = Decimal("5.00")

        elif tipo == "p":
            # pérdida: fijo 20
            extra = Decimal("20.00")

        # retraso puro (r): extra queda 0
        monto = (base + extra).quantize(Decimal("0.01"))

        if monto > Decimal("100.00"):
            messages.error(request, "La multa supera el máximo permitido (100.00).")
            return redirect("crear_multa")

        multa = Multa.objects.create(
            prestamo=prestamo,
            tipo=tipo,
            monto=monto,
            pagada=False,
        )

        return redirect("multa_pago_wizard", multaId=multa.id)

    return render(request, "gestion/templates/crear_multas.html", {"prestamos": prestamos})

@login_required
@require_http_methods(["GET", "POST"])
def multaPagoWizard(request, multaId):
    multa = get_object_or_404(Multa, id=multaId)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "markPaid":
            multa.pagada = True
            multa.fechaPago = timezone.now()
            multa.save()
        elif action == "markPending":
            multa.pagada = False
            multa.fechaPago = None
            multa.save()

        return redirect("lista_multa")

    return render(request, "gestion/templates/multa_pago_wizard.html", {"multa": multa})

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
    paginate_by = 6 # Lista primaria de 10 objetos que se puede ir recorriendo "pestañas de paginas"
    
    def get_queryset(self):
        return Libro.objects.filter(activo=True).order_by('-id')
    
class LibroDetalleView(LoginRequiredMixin, DetailView):
    model = Libro
    template_name = 'gestion/templates/detalle_libros.html'
    context_object_name = 'libro'
    
class LibroCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Libro
    fields = ['titulo', 'autor', 'isbn', 'paginas', 'genero', 'descripcion', 'editorial', 'coverId', 'stock']
    template_name = 'gestion/templates/crear_libros.html'
    success_url = reverse_lazy('lista_libros') #Direcciona a la url que eligamos
    permission_required = 'gestion.add_libro'

class LibroUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Libro
    fields = ['titulo', 'autor', 'isbn', 'paginas', 'genero', 'descripcion', 'editorial', 'coverId', 'stock']
    template_name = 'gestion/templates/editar_libros.html'
    success_url = reverse_lazy('lista_libros')
    permission_required = 'gestion.change_libro'
    
class LibroDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Libro
    template_name = 'gestion/templates/eliminar_libros.html' # Ventana de confirmacion para eliminar
    success_url = reverse_lazy('lista_libros')
    permission_required = 'gestion.delete_libro'

    def post(self, request, *args, **kwargs):
        libro = self.get_object()
        libro.activo = False
        libro.save()
        messages.success(request, "Libro inactivado (se conserva el histórico de préstamos).")
        return redirect(self.success_url)
    
class LibroInactivoListView(LoginRequiredMixin, ListView):
    model = Libro
    template_name = "gestion/templates/libros_inactivos.html"
    context_object_name = "libros"
    paginate_by = 12

    def get_queryset(self):
        return Libro.objects.filter(activo=False).order_by("-id")