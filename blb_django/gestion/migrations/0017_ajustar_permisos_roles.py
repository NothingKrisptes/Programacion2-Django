from django.db import migrations

def ajustar_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    bibli_group = Group.objects.get(name="BIBLIOTECARIO")
    bode_group = Group.objects.get(name="BODEGUERO")
    cliente_group = Group.objects.get(name="CLIENTE")

    perms_libro = Permission.objects.filter(content_type__app_label="gestion", content_type__model="libro")
    perms_prestamo = Permission.objects.filter(content_type__app_label="gestion", content_type__model="prestamo")
    perms_multa = Permission.objects.filter(content_type__app_label="gestion", content_type__model="multa")

    # Cliente: solo ver libros
    cliente_group.permissions.set(list(perms_libro.filter(codename__startswith="view_")))

    # Bibliotecario: ver libros + gestionar prestamos/multas (sin add/change/delete libro)
    bibli_group.permissions.set(
        list(perms_libro.filter(codename__startswith="view_")) +
        list(perms_prestamo) +
        list(perms_multa)
    )

    # Bodeguero: full libro perms
    bode_group.permissions.set(list(perms_libro))

class Migration(migrations.Migration):
    dependencies = [
        ("gestion", "0016_logevento"),
        ("auth", "__latest__"),
    ]

    operations = [
        migrations.RunPython(ajustar_roles),
    ]
