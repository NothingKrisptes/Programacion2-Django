from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.conf import settings
from .models import Autor,Libro,Prestamo,Multa,LogEvento
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
from .services.multas_service import ensure_multa_retraso
from django.contrib.auth.decorators import user_passes_test
from .forms import ClienteRegistroForm, AdminCrearUsuarioForm
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

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
@permission_required("gestion.add_libro", raise_exception=True)
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
@permission_required("gestion.add_libro", raise_exception=True)
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

@login_required
@permission_required("gestion.change_libro", raise_exception=True)
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
@permission_required("gestion.view_autor", raise_exception=True)
def lista_autores(request):
    autores = Autor.objects.filter(activo=True).order_by("apellido", "nombre")
    return render(request, "gestion/templates/autores.html", {"autores": autores})

@login_required
@permission_required("gestion.add_autor", raise_exception=True)
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
@permission_required("gestion.delete_autor", raise_exception=True)
@require_POST
def inactivar_autor(request, id):
    autor = get_object_or_404(Autor, id=id)
    autor.activo = False
    autor.save()
    messages.success(request, "Autor inactivado.")
    return redirect("lista_autores")

@login_required
@permission_required("gestion.gestionar_prestamos", raise_exception=True)
def lista_prestamos(request):
    prestamos = Prestamo.objects.all().order_by("-id")

    # Generar/actualizar multas de retraso para préstamos no devueltos
    for p in prestamos:
        if not p.fecha_devolucion:
            ensure_multa_retraso(p)

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
        log_event(request, "CREAR_PRESTAMO", f"Prestamo #{prestamo.id} | Libro={prestamo.libro_id} | Usuario={prestamo.usuario_id}")

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
@permission_required("gestion.gestionar_prestamos", raise_exception=True)
def detalle_prestamo(request, id):
    prestamo = get_object_or_404(Prestamo, id=id)

    # Al entrar al detalle, asegurar multa de retraso si aplica
    if not prestamo.fecha_devolucion:
        ensure_multa_retraso(prestamo)

    multas = prestamo.Multas.all().order_by("-id")
    return render(request, 'gestion/templates/detalle_prestamo.html', {'prestamo': prestamo, 'multas': multas})

@login_required
@permission_required("gestion.gestionar_prestamos", raise_exception=True)
@require_http_methods(["POST"])
def devolver_prestamo(request, id):
    prestamo = get_object_or_404(Prestamo, id=id)

    if prestamo.fecha_devolucion:
        return redirect("detalle_prestamo", id=prestamo.id)

    prestamo.fecha_devolucion = timezone.now().date()
    prestamo.save()
    log_event(request, "DEVOLVER_PRESTAMO", f"Prestamo #{prestamo.id} devuelto | Libro={prestamo.libro_id}")

    # sumar stock
    Libro.objects.filter(id=prestamo.libro.id).update(stock=F('stock') + 1)
    prestamo.libro.refresh_from_db()
    prestamo.libro.save()  # recalcula disponible

    return redirect("detalle_prestamo", id=prestamo.id)

@login_required
@permission_required("gestion.gestionar_prestamos", raise_exception=True)
def lista_multas(request):
    multas = Multa.objects.all().order_by('-id')
    return render(request, 'gestion/templates/multas.html', {'multas': multas})

@login_required
@permission_required("gestion.gestionar_prestamos", raise_exception=True)
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
        log_event(request, "CREAR_MULTA", f"Multa #{multa.id} | Prestamo={prestamo.id} | Tipo={tipo} | Monto={monto}")

        return redirect("multa_pago_wizard", multaId=multa.id)

    return render(request, "gestion/templates/crear_multas.html", {"prestamos": prestamos})

@login_required
@require_http_methods(["GET", "POST"])
def multaPagoWizard(request, multaId):
    multa = get_object_or_404(Multa, id=multaId)

    # (Opcional) Solo bibliotecario/admin debería poder marcar pagada:
    if not request.user.has_perm("gestion.gestionar_prestamos"):
        return HttpResponseForbidden("No tienes permisos para gestionar pagos de multas.")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "markPaid" and not multa.pagada:
            multa.pagada = True
            multa.fechaPago = timezone.now()
            multa.save()
            log_event(request, "PAGAR_MULTA", f"Multa #{multa.id} pagada | Prestamo={multa.prestamo_id} | Monto={multa.monto}")
        return redirect("lista_multa")

    return render(request, "gestion/templates/multa_pago_wizard.html", {"multa": multa})

def registro(request):
    if request.method == "POST":
        form = ClienteRegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=True)  # el form ya pone first_name/last_name/email

            # Asignación por grupo (rol)
            grupo_cliente = Group.objects.get(name="CLIENTE")
            usuario.groups.add(grupo_cliente)

            login(request, usuario)
            messages.success(request, "Cuenta creada correctamente.")
            return redirect("index")
    else:
        form = ClienteRegistroForm()

    return render(request, "gestion/templates/registration/registro.html", {"form": form})

def error(request):
    return render(request, 'gestion/templates/error.html',{'error':error})

# Administración de usuarios por un admin
def es_admin(user):
    return user.is_authenticated and user.is_superuser

# Helper de logging para los eventos
def log_event(request, accion, detalle=""):
    if request.user.is_authenticated:
        LogEvento.objects.create(
            usuario=request.user,
            accion=accion,
            detalle=detalle
        )

@user_passes_test(es_admin)
def nuevo_usuario(request):
    if request.method == "POST":
        form = AdminCrearUsuarioForm(request.POST)
        if form.is_valid():
            created_user = form.save()  # <- AQUÍ se crea y se obtiene el usuario

            rol = form.cleaned_data.get("rol", "")
            log_event(
                request,
                "CREAR_USUARIO",
                f"Usuario creado: {created_user.username} | Rol={rol}"
            )

            messages.success(request, "Usuario creado correctamente.")
            return redirect("index")
    else:
        form = AdminCrearUsuarioForm()

    return render(request, "gestion/templates/nuevo_usuario.html", {"form": form})

@user_passes_test(es_admin)
def reporte_libros_prestados_pdf(request):
    # Prestamos activos (no devueltos)
    prestamos = (Prestamo.objects
                 .filter(fecha_devolucion__isnull=True)
                 .select_related("libro", "usuario")
                 .order_by("fecha_max"))

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="reporte_libros_prestados.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    y = height - 1 * inch
    p.setFont("Helvetica-Bold", 14)
    p.drawString(1 * inch, y, "Reporte: Libros prestados (activos)")
    y -= 0.3 * inch

    p.setFont("Helvetica", 10)
    p.drawString(1 * inch, y, f"Generado: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
    y -= 0.4 * inch

    p.setFont("Helvetica-Bold", 10)
    p.drawString(1 * inch, y, "ID")
    p.drawString(1.5 * inch, y, "Usuario")
    p.drawString(3.2 * inch, y, "Libro")
    p.drawString(5.8 * inch, y, "Máxima")
    y -= 0.2 * inch
    p.line(1 * inch, y, 7.5 * inch, y)
    y -= 0.25 * inch

    p.setFont("Helvetica", 10)
    for pr in prestamos:
        if y < 1 * inch:
            p.showPage()
            y = height - 1 * inch
            p.setFont("Helvetica", 10)

        p.drawString(1 * inch, y, str(pr.id))
        p.drawString(1.5 * inch, y, pr.usuario.username)
        p.drawString(3.2 * inch, y, str(pr.libro)[:35])
        p.drawString(5.8 * inch, y, str(pr.fecha_max))
        y -= 0.22 * inch

    p.showPage()
    p.save()
    return response

@user_passes_test(es_admin)
def reporte_usuarios_multados_pdf(request):
    # Usuarios con multas pendientes
    multas = (Multa.objects
              .filter(pagada=False)
              .select_related("prestamo__usuario", "prestamo__libro")
              .order_by("prestamo__usuario__username", "-fecha"))

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="reporte_usuarios_multados.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    y = height - 1 * inch
    p.setFont("Helvetica-Bold", 14)
    p.drawString(1 * inch, y, "Reporte: Usuarios con multas pendientes")
    y -= 0.3 * inch

    p.setFont("Helvetica", 10)
    p.drawString(1 * inch, y, f"Generado: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
    y -= 0.4 * inch

    p.setFont("Helvetica-Bold", 10)
    p.drawString(1 * inch, y, "Usuario")
    p.drawString(2.8 * inch, y, "Préstamo")
    p.drawString(4.6 * inch, y, "Tipo")
    p.drawString(5.5 * inch, y, "Monto")
    y -= 0.2 * inch
    p.line(1 * inch, y, 7.5 * inch, y)
    y -= 0.25 * inch

    p.setFont("Helvetica", 10)
    for m in multas:
        if y < 1 * inch:
            p.showPage()
            y = height - 1 * inch
            p.setFont("Helvetica", 10)

        usuario = m.prestamo.usuario.username
        prestamo = f"#{m.prestamo.id} {str(m.prestamo.libro)[:20]}"
        p.drawString(1 * inch, y, usuario)
        p.drawString(2.8 * inch, y, prestamo)
        p.drawString(4.6 * inch, y, m.get_tipo_display())
        p.drawRightString(6.6 * inch, y, str(m.monto))
        y -= 0.22 * inch

    p.showPage()
    p.save()
    return response

@user_passes_test(es_admin)
def reporte_multas_total_pdf(request):
    multas = (Multa.objects
              .select_related("prestamo__usuario", "prestamo__libro")
              .order_by("-fecha", "-id"))

    total = sum([m.monto for m in multas])
    total_pendiente = sum([m.monto for m in multas if not m.pagada])
    total_pagado = sum([m.monto for m in multas if m.pagada])

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="reporte_multas_total.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    y = height - 1 * inch
    p.setFont("Helvetica-Bold", 14)
    p.drawString(1 * inch, y, "Reporte: Multas (total)")
    y -= 0.3 * inch

    p.setFont("Helvetica", 10)
    p.drawString(1 * inch, y, f"Generado: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
    y -= 0.3 * inch
    p.drawString(1 * inch, y, f"Total: {total}")
    y -= 0.2 * inch
    p.drawString(1 * inch, y, f"Total pagado: {total_pagado}")
    y -= 0.2 * inch
    p.drawString(1 * inch, y, f"Total pendiente: {total_pendiente}")
    y -= 0.35 * inch

    p.setFont("Helvetica-Bold", 10)
    p.drawString(1 * inch, y, "ID")
    p.drawString(1.5 * inch, y, "Usuario")
    p.drawString(3.1 * inch, y, "Libro")
    p.drawString(5.3 * inch, y, "Estado")
    p.drawString(6.2 * inch, y, "Monto")
    y -= 0.2 * inch
    p.line(1 * inch, y, 7.5 * inch, y)
    y -= 0.25 * inch

    p.setFont("Helvetica", 10)
    for m in multas:
        if y < 1 * inch:
            p.showPage()
            y = height - 1 * inch
            p.setFont("Helvetica", 10)

        estado = "Pagada" if m.pagada else "Pendiente"
        p.drawString(1 * inch, y, str(m.id))
        p.drawString(1.5 * inch, y, m.prestamo.usuario.username)
        p.drawString(3.1 * inch, y, str(m.prestamo.libro)[:25])
        p.drawString(5.3 * inch, y, estado)
        p.drawRightString(7.2 * inch, y, str(m.monto))
        y -= 0.22 * inch

    p.showPage()
    p.save()
    return response

@user_passes_test(es_admin)
def ver_logs(request):
    logs = LogEvento.objects.select_related("usuario").order_by("-fecha")[:500]
    return render(request, "gestion/templates/logs.html", {"logs": logs})

# TIPO DE VISTAS VERSION DJGANGO
# Se necesitan las siguientes librerias
# from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
# from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
# from django.urls import reverse_lazy

class LibroListView(ListView):
    model = Libro
    template_name = 'gestion/templates/libros_view.html'
    context_object_name = 'libros'
    paginate_by = 6 # Lista primaria de 10 objetos que se puede ir recorriendo "pestañas de paginas"
    
    def get_queryset(self):
        return Libro.objects.filter(activo=True).order_by('-id')
     
class LibroDetalleView(DetailView):
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