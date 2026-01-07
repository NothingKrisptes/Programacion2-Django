# gestion/migrations/0002_roles_permisos.py
from django.db import migrations

def crear_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    # Crea grupos
    admin_group, _ = Group.objects.get_or_create(name="ADMIN")
    bibli_group, _ = Group.objects.get_or_create(name="BIBLIOTECARIO")
    bode_group, _ = Group.objects.get_or_create(name="BODEGUERO")
    cliente_group, _ = Group.objects.get_or_create(name="CLIENTE")

    # Permisos por defecto (Django crea add/change/delete/view)
    # Libro: bodeguero y bibliotecario pueden ver; bodeguero gestiona stock/libros
    perms_libro = Permission.objects.filter(content_type__app_label="gestion", content_type__model="libro")
    perms_autor = Permission.objects.filter(content_type__app_label="gestion", content_type__model="autor")
    perms_prestamo = Permission.objects.filter(content_type__app_label="gestion", content_type__model="prestamo")
    perms_multa = Permission.objects.filter(content_type__app_label="gestion", content_type__model="multa")

    # Cliente: solo ver libros/autores y ver sus cosas vía vistas (no permisos de modelo para editar)
    cliente_group.permissions.set(list(perms_libro.filter(codename__startswith="view_")) + list(perms_autor.filter(codename__startswith="view_")))

    # Bibliotecario: ver libros/autores + gestionar prestamos/multas
    bibli_group.permissions.set(
        list(perms_libro.filter(codename__startswith="view_")) +
        list(perms_autor.filter(codename__startswith="view_")) +
        list(perms_prestamo) +
        list(perms_multa)
    )

    # Bodeguero: gestionar libros/autores (según tu criterio)
    bode_group.permissions.set(list(perms_libro) + list(perms_autor.filter(codename__startswith="view_")))

    # ADMIN (grupo) puede tener todos los permisos de la app; el superuser igual ya los tiene
    all_gestion_perms = Permission.objects.filter(content_type__app_label="gestion")
    admin_group.permissions.set(list(all_gestion_perms))

class Migration(migrations.Migration):
    dependencies = [
        ("gestion", "0014_multa_uniq_multa_por_prestamo_y_tipo"),  # ajusta si tu 0001 se llama distinto
        ("auth", "__latest__"),
    ]

    operations = [
        migrations.RunPython(crear_roles),
    ]
